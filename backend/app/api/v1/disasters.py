"""
app/api/v1/disasters.py

Disaster Management router — complete production implementation.

Prefix : /api/v1/disasters
Tags   : Disasters

Endpoint map
------------
POST  /                     → Create a new disaster event       (Government)
GET   /                     → List all disasters                (Public)
GET   /search               → Search/filter disasters           (Public)
GET   /{disaster_id}        → Get a single disaster by UUID     (Public)
PUT   /{disaster_id}        → Full update of a disaster         (Government)
DELETE /{disaster_id}       → Soft-delete a disaster            (Government)
PATCH /{disaster_id}/verify   → Verify (reported → verified)   (Government)
PATCH /{disaster_id}/severity → Update severity level          (Government)
PATCH /{disaster_id}/status   → Update lifecycle status        (Government)

Route ordering note
-------------------
GET /search is declared BEFORE GET /{disaster_id} so FastAPI does not
incorrectly route /disasters/search into the parametrised handler.

Permissions
-----------
Government : Full CRUD + all PATCH operations
NGO        : Read-only (uses public GET endpoints)
Volunteer  : Read-only
Hospital   : Read-only
Citizen    : Read-only (public endpoints)
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment
from app.database.session import get_db
from app.models.enums import DisasterSeverity, DisasterStatus
from app.schemas.disaster import DisasterCreate, DisasterResponse, DisasterUpdate
from app.schemas.patch import DisasterStatusPatch, SeverityPatch
from app.services import disaster_service, need_score_service, priority_service
from app.utils.constants import (
    API_V1_TAG_DISASTERS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/disasters",
    tags=[API_V1_TAG_DISASTERS],
)


# ---------------------------------------------------------------------------
# Private serialisation helpers
# ---------------------------------------------------------------------------

def _serialize(disaster: Any) -> dict[str, Any]:
    """Convert a Disaster ORM instance to a JSON-serialisable dict."""
    return DisasterResponse.model_validate(disaster).model_dump(mode="json")


def _serialize_list(disasters: list[Any]) -> list[dict[str, Any]]:
    """Bulk serialise a list of Disaster ORM instances."""
    return [_serialize(d) for d in disasters]


# ---------------------------------------------------------------------------
# Common query parameter descriptions (DRY)
# ---------------------------------------------------------------------------
_SORT_BY_DESCRIPTION = (
    "Field to sort results by. "
    "Options: created_at (default) | newest | oldest | title | severity | status."
)
_SORT_ORDER_DESCRIPTION = "Sort direction: desc (default) | asc. Ignored when sort_by=oldest."


# ===========================================================================
# PUBLIC ENDPOINTS — no authentication required
# ===========================================================================

@router.get(
    "/search",
    summary="Search disaster events",
    description="""
Search and filter disaster events by keyword, location, severity, status, and type.

- **q**: Full-text search across title, description, and district
- All other parameters are optional additional filters
- Results are paginated and sortable

No authentication required.
    """,
)
async def search_disasters(
    db: Annotated[Session, Depends(get_db)],
    q: Optional[str] = Query(
        None,
        description="Keyword search — matches disaster title, description, and district.",
    ),
    severity: Optional[DisasterSeverity] = Query(
        None,
        description="Filter by severity level: low | medium | high | critical.",
    ),
    filter_status: Optional[DisasterStatus] = Query(
        None,
        alias="status",
        description="Filter by lifecycle status: reported | verified | resource_allocated | rescue_ongoing | resolved.",
    ),
    district: Optional[str] = Query(
        None,
        description="Filter by district (case-insensitive partial match).",
    ),
    state: Optional[str] = Query(
        None,
        description="Filter by state or province (partial match).",
    ),
    disaster_type: Optional[str] = Query(
        None,
        description="Filter by disaster type, e.g. 'flood', 'earthquake', 'cyclone'.",
    ),
    sort_by: str = Query("created_at", description=_SORT_BY_DESCRIPTION),
    sort_order: str = Query("desc", description=_SORT_ORDER_DESCRIPTION),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
) -> Any:
    disasters, total = disaster_service.list_disasters(
        db=db,
        search=q,
        severity=severity,
        disaster_status=filter_status,
        district=district,
        state=state,
        disaster_type=disaster_type,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(disasters),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Search returned {total} result(s).",
    )


@router.get(
    "/need-scores",
    summary="Rank active disasters by computed need score",
    description="""
Compute and rank all active disasters by a composite **need score** (0-100).

The score blends four signals: the government-assessed severity, the volume
of citizen emergency reports linked to the disaster, how depleted its
assigned resources are, and how early/stalled it is in the response
lifecycle. Each disaster's response includes a `breakdown` showing every
component's contribution, so the ranking is fully explainable.

Resolved disasters are excluded by default — pass `include_resolved=true`
to include them (they will always score at or near the bottom).

No authentication required — read-only, useful to every role for
prioritising where to act next.
    """,
)
async def get_need_scores(
    db: Annotated[Session, Depends(get_db)],
    include_resolved: bool = Query(
        False,
        description="Include RESOLVED disasters in the ranking (they score lowest).",
    ),
) -> Any:
    ranked = need_score_service.rank_disasters_by_need(db, include_resolved=include_resolved)
    return success_response(
        data=[item.model_dump(mode="json") for item in ranked],
        message=f"Computed need scores for {len(ranked)} disaster(s).",
    )


@router.get(
    "/distribution-priority",
    summary="Rank active disasters by urgency + accessibility",
    description="""
Compute and rank all active disasters by a **distribution priority score**
that combines urgency (the same need score as `/disasters/need-scores`,
weight 0.6) with **accessibility** (straight-line proximity to the nearest
registered shelter and hospital, weight 0.4).

This directly answers "where should limited relief resources go first,
given both how badly they're needed and how quickly we can actually get
them there." Each response includes the nearest shelter/hospital and their
distances so the ranking is fully explainable.

No authentication required — read-only.
    """,
)
async def get_distribution_priority(
    db: Annotated[Session, Depends(get_db)],
    include_resolved: bool = Query(
        False,
        description="Include RESOLVED disasters in the ranking.",
    ),
) -> Any:
    ranked = priority_service.rank_by_distribution_priority(db, include_resolved=include_resolved)
    return success_response(
        data=[item.model_dump(mode="json") for item in ranked],
        message=f"Computed distribution priority for {len(ranked)} disaster(s).",
    )


@router.get(
    "/",
    summary="List all disaster events",
    description="""
Retrieve a paginated list of all active (non-deleted) disaster events.

Supports:
- **Filtering** by severity, status, district, state, and type
- **Date range** with from_date and to_date
- **Full-text search** via the `search` parameter
- **Sorting** by any major field
- **Pagination** with configurable page size

No authentication required — publicly accessible to citizens and all roles.
    """,
)
async def list_disasters(
    db: Annotated[Session, Depends(get_db)],
    severity: Optional[DisasterSeverity] = Query(
        None,
        description="Filter by severity level: low | medium | high | critical.",
    ),
    filter_status: Optional[DisasterStatus] = Query(
        None,
        alias="status",
        description="Filter by lifecycle status.",
    ),
    district: Optional[str] = Query(
        None,
        description="Filter by district (partial, case-insensitive).",
    ),
    state: Optional[str] = Query(
        None,
        description="Filter by state or province (partial match).",
    ),
    disaster_type: Optional[str] = Query(
        None,
        description="Filter by disaster type (e.g. 'flood', 'cyclone').",
    ),
    search: Optional[str] = Query(
        None,
        description="Full-text keyword search across title, description, and district.",
    ),
    from_date: Optional[datetime] = Query(
        None,
        description="Return only disasters created on or after this datetime (ISO 8601).",
    ),
    to_date: Optional[datetime] = Query(
        None,
        description="Return only disasters created on or before this datetime (ISO 8601).",
    ),
    sort_by: str = Query("created_at", description=_SORT_BY_DESCRIPTION),
    sort_order: str = Query("desc", description=_SORT_ORDER_DESCRIPTION),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
) -> Any:
    disasters, total = disaster_service.list_disasters(
        db=db,
        severity=severity,
        disaster_status=filter_status,
        district=district,
        state=state,
        disaster_type=disaster_type,
        search=search,
        from_date=from_date,
        to_date=to_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(disasters),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(disasters)} of {total} disaster event(s).",
    )


@router.get(
    "/{disaster_id}",
    summary="Get a disaster event by ID",
    description="""
Retrieve full details of a specific disaster event by its UUID.

Returns HTTP 404 if the disaster does not exist or has been deleted.
No authentication required.
    """,
)
async def get_disaster(
    disaster_id: Annotated[UUID, Path(description="UUID of the disaster to retrieve.")],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    disaster = disaster_service.get_disaster_by_id(db, disaster_id)
    return success_response(
        data=_serialize(disaster),
        message="Disaster retrieved successfully.",
    )


# ===========================================================================
# PROTECTED ENDPOINTS — Government role required
# ===========================================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new disaster event",
    description="""
Register a new disaster event in the ResQMesh platform.

- The authenticated user's ID is automatically recorded as the reporter
- Status defaults to **reported** if not specified
- Country defaults to **India** if not specified

Requires: **Government** role.
    """,
)
async def create_disaster(
    data: DisasterCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    disaster = disaster_service.create_disaster(db, data, current_user.id)
    return success_response(
        data=_serialize(disaster),
        message="Disaster event created and recorded successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/{disaster_id}",
    summary="Update a disaster event",
    description="""
Update fields of an existing disaster record.

Only fields included in the request body are modified — omitted fields retain their current values.

Requires: **Government** role.
    """,
)
async def update_disaster(
    disaster_id: Annotated[UUID, Path(description="UUID of the disaster to update.")],
    data: DisasterUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    disaster = disaster_service.update_disaster(db, disaster_id, data)
    return success_response(
        data=_serialize(disaster),
        message="Disaster updated successfully.",
    )


@router.delete(
    "/{disaster_id}",
    summary="Delete a disaster event",
    description="""
Soft-delete a disaster event (sets `is_deleted = true`).

The record is retained in the database for audit and reporting purposes.
It will no longer appear in any list or search results.

Requires: **Government** role.
    """,
)
async def delete_disaster(
    disaster_id: Annotated[UUID, Path(description="UUID of the disaster to delete.")],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    disaster_service.delete_disaster(db, disaster_id)
    return success_response(message="Disaster deleted successfully.")


@router.patch(
    "/{disaster_id}/verify",
    summary="Verify a reported disaster",
    description="""
Transition a disaster from **reported** → **verified** status.

Verification confirms that the disaster event has been assessed and is real.
Only disasters currently in `reported` status can be verified.

Requires: **Government** role.
    """,
)
async def verify_disaster(
    disaster_id: Annotated[UUID, Path(description="UUID of the disaster to verify.")],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    disaster = disaster_service.verify_disaster(db, disaster_id)
    return success_response(
        data=_serialize(disaster),
        message="Disaster verified. Status updated to 'verified'.",
    )


@router.patch(
    "/{disaster_id}/severity",
    summary="Update disaster severity level",
    description="""
Update the assessed severity level of a disaster event.

Valid severity levels: **low** | **medium** | **high** | **critical**

Requires: **Government** role.
    """,
)
async def update_severity(
    disaster_id: Annotated[UUID, Path(description="UUID of the disaster.")],
    data: SeverityPatch,
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    disaster = disaster_service.update_severity(db, disaster_id, data.severity)
    return success_response(
        data=_serialize(disaster),
        message=f"Disaster severity updated to '{data.severity.value}'.",
    )


@router.patch(
    "/{disaster_id}/status",
    summary="Update disaster lifecycle status",
    description="""
Manually set the lifecycle status of a disaster event.

Valid statuses:
- **reported** — initial state after report submission
- **verified** — confirmed as a real disaster by authorities
- **resource_allocated** — relief resources have been deployed
- **rescue_ongoing** — active rescue operations in progress
- **resolved** — disaster resolved, response concluded

Requires: **Government** role.
    """,
)
async def update_status(
    disaster_id: Annotated[UUID, Path(description="UUID of the disaster.")],
    data: DisasterStatusPatch,
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    disaster = disaster_service.update_status(db, disaster_id, data.status)
    return success_response(
        data=_serialize(disaster),
        message=f"Disaster status updated to '{data.status.value}'.",
    )
