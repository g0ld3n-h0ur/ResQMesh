"""
app/api/v1/reports.py

Emergency Report router — complete production implementation.

Prefix : /api/v1/reports
Tags   : Reports

Endpoint map
------------
POST  /emergency                → Submit a public emergency report    (Public — no auth)
GET   /                         → List all reports with filters        (Government)
GET   /{report_id}              → Retrieve a single report by UUID     (Government)
PATCH /{report_id}/verify       → Verify a report + link to disaster   (Government)
DELETE /{report_id}             → Soft-delete a report                 (Government)

Route ordering note
-------------------
GET /emergency (if ever needed as GET) and all fixed-path routes are declared
BEFORE the parametrised /{report_id} handler to prevent routing conflicts.
Currently POST /emergency is distinct from GET /{report_id} so no conflict exists.

Permissions
-----------
Public (unauthenticated) : POST /emergency
Government only          : GET /, GET /{id}, PATCH /{id}/verify, DELETE /{id}
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment
from app.database.session import get_db
from app.schemas.emergency_report import (
    EmergencyReportCreate,
    EmergencyReportResponse,
    ReportVerifyRequest,
)
from app.services import report_service
from app.utils.constants import (
    API_V1_TAG_REPORTS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/reports",
    tags=[API_V1_TAG_REPORTS],
)


# ---------------------------------------------------------------------------
# Private serialisation helpers
# ---------------------------------------------------------------------------


def _serialize(report: Any) -> dict[str, Any]:
    """Convert an EmergencyReport ORM instance to a JSON-serialisable dict."""
    return EmergencyReportResponse.model_validate(report).model_dump(mode="json")


def _serialize_list(reports: list[Any]) -> list[dict[str, Any]]:
    """Bulk serialise a list of EmergencyReport ORM instances."""
    return [_serialize(r) for r in reports]


# ---------------------------------------------------------------------------
# Common query parameter descriptions (DRY)
# ---------------------------------------------------------------------------
_SORT_BY_DESCRIPTION = (
    "Sort mode. Options: newest (default) | oldest | verified_first."
)


# ===========================================================================
# PUBLIC ENDPOINT — no authentication required
# ===========================================================================


@router.post(
    "/emergency",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a public emergency report",
    description="""
Submit an emergency incident report without requiring any login or account.

This endpoint is **publicly accessible** — citizens, bystanders, and field
responders can report emergencies directly from the field.

### What to include
- **reporter_name**: Your full name (required)
- **phone**: Contact number for follow-up (optional but strongly recommended)
- **description**: Clear description of what is happening (required)
- **latitude / longitude**: GPS coordinates of the incident — both must be
  provided together or both omitted
- **disaster_type**: Type of emergency, e.g. `flood`, `earthquake`, `fire`, `cyclone`
- **image_url**: URL to a photo or video documenting the scene
- **address**: Human-readable location (landmark, street, village, district)

### Duplicate protection
Identical reports from the same reporter submitted within **10 minutes** are
automatically rejected to prevent accidental double submissions.

### After submission
Government officials will review and verify the report, optionally linking it
to an active disaster event in the ResQMesh platform.

**No authentication required.**
    """,
    response_description="Emergency report created and queued for government review.",
    openapi_extra={"security": []},
)
async def submit_emergency_report(
    data: Annotated[
        EmergencyReportCreate,
        Body(
            openapi_examples={
                "flood_report": {
                    "summary": "Flood emergency in Chennai",
                    "value": {
                        "reporter_name": "Ravi Kumar",
                        "phone": "+919876543210",
                        "description": (
                            "Major flooding on Anna Salai road. Water level is "
                            "above knee height. Several vehicles stranded. "
                            "Residents trapped in ground-floor homes."
                        ),
                        "latitude": 13.0827,
                        "longitude": 80.2707,
                        "disaster_type": "flood",
                        "address": "Anna Salai, Teynampet, Chennai, Tamil Nadu",
                        "image_url": "https://cdn.resqmesh.in/reports/img_abc123.jpg",
                    },
                },
                "earthquake_report": {
                    "summary": "Earthquake in Coimbatore",
                    "value": {
                        "reporter_name": "Priya Sharma",
                        "phone": "+919500001234",
                        "description": (
                            "Strong tremors felt for approximately 30 seconds. "
                            "Multiple buildings showing cracks. People evacuating."
                        ),
                        "latitude": 11.0168,
                        "longitude": 76.9558,
                        "disaster_type": "earthquake",
                        "address": "RS Puram, Coimbatore, Tamil Nadu",
                    },
                },
                "minimal_report": {
                    "summary": "Minimal anonymous report",
                    "value": {
                        "reporter_name": "Anonymous",
                        "description": "Fire in a warehouse near the railway station.",
                        "disaster_type": "fire",
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    report = report_service.create_report(db=db, data=data)
    return success_response(
        data=_serialize(report),
        message=(
            "Emergency report submitted successfully. "
            "Government officials will review your report shortly."
        ),
        status_code=status.HTTP_201_CREATED,
    )


# ===========================================================================
# PROTECTED ENDPOINTS — Government role required
# ===========================================================================


@router.get(
    "/",
    summary="List all emergency reports",
    description="""
Retrieve a paginated list of all active (non-deleted) emergency reports.

### Filtering
- **district / state / country**: Substring match against the report's `address` field
- **date_from / date_to**: Filter reports by submission date range (ISO 8601)
- **is_verified**: `true` = only verified reports | `false` = only unverified | omit = all
- **disaster_type**: Filter by disaster category (e.g. `flood`, `earthquake`)

### Search
- **search**: Full-text keyword search across `reporter_name`, `description`,
  `phone`, `address`, and `disaster_type`

### Sorting
- **sort_by**: `newest` (default) | `oldest` | `verified_first`

### Pagination
Supports both page-based and offset-based pagination:
- Page-based: `page` + `page_size` parameters (default)
- Offset-based: `limit` + `offset` parameters (takes precedence when both provided)

Requires: **Government** role.
    """,
)
async def list_reports(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
    # --- Filters ---
    district: Optional[str] = Query(
        None,
        description="Filter by district — substring match on address field.",
    ),
    state: Optional[str] = Query(
        None,
        description="Filter by state — substring match on address field.",
    ),
    country: Optional[str] = Query(
        None,
        description="Filter by country — substring match on address field.",
    ),
    date_from: Optional[datetime] = Query(
        None,
        description="Return reports submitted on or after this datetime (ISO 8601).",
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="Return reports submitted on or before this datetime (ISO 8601).",
    ),
    is_verified: Optional[bool] = Query(
        None,
        description=(
            "Filter by verification status. "
            "true = verified only | false = unverified only | omit = all."
        ),
    ),
    disaster_type: Optional[str] = Query(
        None,
        description="Filter by disaster category, e.g. 'flood', 'earthquake', 'fire'.",
    ),
    # --- Search ---
    search: Optional[str] = Query(
        None,
        description=(
            "Full-text keyword search across reporter_name, description, "
            "phone, address, and disaster_type."
        ),
    ),
    # --- Sorting ---
    sort_by: str = Query(
        "newest",
        description=_SORT_BY_DESCRIPTION,
    ),
    # --- Page-based pagination ---
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
    # --- Offset-based pagination (overrides page/page_size when both provided) ---
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=(
            f"Raw SQL LIMIT (max {MAX_PAGE_SIZE}). "
            "When combined with `offset`, overrides page/page_size."
        ),
    ),
    offset: Optional[int] = Query(
        None,
        ge=0,
        description="Raw SQL OFFSET. Must be combined with `limit`.",
    ),
) -> Any:
    reports, total = report_service.list_reports(
        db=db,
        district=district,
        state=state,
        country=country,
        date_from=date_from,
        date_to=date_to,
        is_verified=is_verified,
        disaster_type=disaster_type,
        search=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        limit=limit,
        offset=offset,
    )
    return paginated_response(
        data=_serialize_list(reports),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(reports)} of {total} emergency report(s).",
    )


@router.get(
    "/{report_id}",
    summary="Get an emergency report by ID",
    description="""
Retrieve the full details of a specific emergency report by its UUID.

Returns **HTTP 404** if the report does not exist or has been soft-deleted.

Requires: **Government** role.
    """,
)
async def get_report(
    report_id: Annotated[
        UUID,
        Path(description="UUID of the emergency report to retrieve."),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    report = report_service.get_report_by_id(db=db, report_id=report_id)
    return success_response(
        data=_serialize(report),
        message="Emergency report retrieved successfully.",
    )


@router.patch(
    "/{report_id}/verify",
    summary="Verify an emergency report",
    description="""
Mark an emergency report as verified by a Government officer.

### Verification semantics
Verification is performed by linking the report to an existing verified
disaster event in the ResQMesh platform (`disaster_id`). Once linked:
- The report's `linked_disaster_id` is set to the provided disaster UUID
- The response `is_verified` field becomes `true`
- The report will appear in the **verified** filter results

### Rules
- A `disaster_id` is **required** to verify a report
- Reports that are **already verified** cannot be re-verified
- The linked disaster must already exist in the system (FK constraint enforced by DB)
- Soft-deleted reports cannot be verified

Requires: **Government** role.
    """,
    response_description="Report verified and linked to the specified disaster.",
)
async def verify_report(
    report_id: Annotated[
        UUID,
        Path(description="UUID of the emergency report to verify."),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
    payload: ReportVerifyRequest = Body(
        ...,
        openapi_examples={
            "verify_with_disaster": {
                "summary": "Verify and link to an existing disaster",
                "value": {
                    "disaster_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "notes": "Field team confirmed flooding in the reported sector.",
                },
            },
        },
    ),
) -> Any:
    report = report_service.verify_report(
        db=db,
        report_id=report_id,
        payload=payload,
        verified_by=current_user.id,
    )
    return success_response(
        data=_serialize(report),
        message=(
            f"Emergency report verified and linked to "
            f"disaster '{report.linked_disaster_id}'."
        ),
    )


@router.delete(
    "/{report_id}",
    summary="Delete an emergency report",
    description="""
Soft-delete an emergency report (sets `is_deleted = true`).

The record is **retained** in the database for audit and incident history
purposes. It will no longer appear in any list, search, or retrieval results.

### When to delete
- Duplicate or accidental submissions
- Clearly false or malicious reports
- Reports superseded by a formal disaster record

Requires: **Government** role.
    """,
    response_description="Report soft-deleted successfully.",
)
async def delete_report(
    report_id: Annotated[
        UUID,
        Path(description="UUID of the emergency report to delete."),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    report_service.delete_report(
        db=db,
        report_id=report_id,
        deleted_by=current_user.id,
    )
    return success_response(
        message="Emergency report deleted successfully.",
    )
