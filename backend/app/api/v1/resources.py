"""
app/api/v1/resources.py

Resource Management router — complete production implementation.

Prefix : /api/v1/resources
Tags   : Resources

Endpoint map
------------
POST  /                     → Register a new resource             (Government)
GET   /                     → List all resources with filters      (Gov + NGO + Volunteer)
GET   /{resource_id}        → Retrieve a single resource by UUID   (Gov + NGO + Volunteer)
PUT   /{resource_id}        → Full update of a resource record     (Government)
DELETE /{resource_id}       → Soft-delete a resource               (Government)
PATCH /{resource_id}/allocate → Allocate to a disaster             (Gov + NGO)
PATCH /{resource_id}/release  → Release allocation back to stock   (Government)

Route ordering note
-------------------
All fixed-path sub-routes (/allocate, /release) are impossible to confuse with
/{resource_id} because they are declared under the same parameterised base URL —
FastAPI resolves them correctly via HTTP method + full path matching.

Permissions
-----------
Government : Full CRUD + allocate + release
NGO        : Read (list, get) + allocate
Volunteer  : Read only (list, get)
Citizen    : No access (no endpoint exposed to them)
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment, require_role
from app.database.session import get_db
from app.models.enums import ResourceStatus, RoleEnum
from app.models.user import User
from app.schemas.resource import (
    AllocateRequest,
    ReleaseRequest,
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
)
from app.schemas.allocation_suggestion import AllocationSuggestionItem
from app.services import allocation_service, resource_service
from app.utils.constants import (
    API_V1_TAG_RESOURCES,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/resources",
    tags=[API_V1_TAG_RESOURCES],
)

# ---------------------------------------------------------------------------
# Multi-role permission aliases (built inline — no modifications to permissions.py)
# ---------------------------------------------------------------------------
# Government or NGO — read + allocate operations
_RequireGovOrNGO = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO)),
]

# Government, NGO, or Volunteer — read-only operations
_RequireReadAccess = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO, RoleEnum.VOLUNTEER)),
]


# ---------------------------------------------------------------------------
# Private serialisation helpers
# ---------------------------------------------------------------------------


def _serialize(resource: Any) -> dict[str, Any]:
    """Convert a Resource ORM instance to a JSON-serialisable dict."""
    return ResourceResponse.model_validate(resource).model_dump(mode="json")


def _serialize_list(resources: list[Any]) -> list[dict[str, Any]]:
    """Bulk serialise a list of Resource ORM instances."""
    return [_serialize(r) for r in resources]


# ---------------------------------------------------------------------------
# Sort description (DRY)
# ---------------------------------------------------------------------------
_SORT_BY_DESCRIPTION = (
    "Sort field. Options: newest (default) | oldest | type | status | quantity."
)


# ===========================================================================
# GOVERNMENT-ONLY — write operations
# ===========================================================================


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new resource",
    description="""
Register a new relief resource item into the ResQMesh inventory.

### Supported resource types
`food` | `water` | `medicine` | `blankets` | `vehicles` | `fuel` |
`medical_kit` | `generator`

### Quantity rules
- `quantity` — total units in stock (must be ≥ 0)
- `available_quantity` — units currently available for allocation
  (must be ≥ 0 and ≤ `quantity`)
- `status` defaults to `available`

### Optional disaster assignment
Provide `assigned_disaster` to immediately link this resource to an
active disaster event at creation time.

Requires: **Government** role.
    """,
)
async def create_resource(
    data: Annotated[
        ResourceCreate,
        Body(
            openapi_examples={
                "water_supply": {
                    "summary": "Water supply depot",
                    "value": {
                        "resource_type": "water",
                        "quantity": 5000,
                        "available_quantity": 5000,
                        "location": "Chennai Central Depot, Tamil Nadu",
                        "status": "available",
                    },
                },
                "medical_kit_allocated": {
                    "summary": "Medical kits already assigned to a disaster",
                    "value": {
                        "resource_type": "medical_kit",
                        "quantity": 200,
                        "available_quantity": 120,
                        "location": "Coimbatore Field Base",
                        "status": "allocated",
                        "assigned_disaster": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    resource = resource_service.create_resource(db=db, data=data)
    return success_response(
        data=_serialize(resource),
        message="Resource registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/{resource_id}",
    summary="Update a resource record",
    description="""
Perform a full (or partial) update on an existing resource record.

Only fields included in the request body are modified — omitted fields
retain their current values.

### Quantity invariant
`available_quantity` must not exceed `quantity` after the update.
The service enforces this across the merged (existing + patch) values.

Requires: **Government** role.
    """,
)
async def update_resource(
    resource_id: Annotated[UUID, Path(description="UUID of the resource to update.")],
    data: ResourceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    resource = resource_service.update_resource(db=db, resource_id=resource_id, data=data)
    return success_response(
        data=_serialize(resource),
        message="Resource updated successfully.",
    )


@router.delete(
    "/{resource_id}",
    summary="Delete a resource record",
    description="""
Soft-delete a resource record (`is_deleted = true`).

The record is retained in the database for audit purposes and will no
longer appear in any list, search, or retrieval results.

### Constraint
Resources with status `allocated` or `in_transit` **cannot** be deleted.
Release the resource first using `PATCH /{id}/release`.

Requires: **Government** role.
    """,
)
async def delete_resource(
    resource_id: Annotated[UUID, Path(description="UUID of the resource to delete.")],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    resource_service.delete_resource(db=db, resource_id=resource_id)
    return success_response(message="Resource deleted successfully.")


@router.patch(
    "/{resource_id}/release",
    summary="Release allocated resource back to stock",
    description="""
Release a quantity of an allocated resource back into available stock.

### Business rules
- Resource must be in `allocated` or `in_transit` status.
- `quantity_to_release` must be ≥ 1 and ≤ currently allocated quantity.
- `available_quantity` is incremented by the released amount.
- When all units are released, `status` reverts to `available` and
  `assigned_disaster` is cleared automatically.

Requires: **Government** role.
    """,
)
async def release_resource(
    resource_id: Annotated[UUID, Path(description="UUID of the resource to release.")],
    payload: Annotated[
        ReleaseRequest,
        Body(
            openapi_examples={
                "partial_release": {
                    "summary": "Release 50 units back to stock",
                    "value": {"quantity_to_release": 50},
                },
                "full_release": {
                    "summary": "Release all 200 units",
                    "value": {"quantity_to_release": 200},
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    resource = resource_service.release_resource(
        db=db,
        resource_id=resource_id,
        quantity_to_release=payload.quantity_to_release,
    )
    return success_response(
        data=_serialize(resource),
        message=(
            f"Released {payload.quantity_to_release} unit(s). "
            f"Available stock is now {resource.available_quantity}."
        ),
    )


# ===========================================================================
# GOVERNMENT + NGO — read + allocate operations
# ===========================================================================


@router.patch(
    "/{resource_id}/allocate",
    summary="Allocate resource to a disaster",
    description="""
Allocate a quantity of a resource to a specific disaster event.

### Business rules
- Resource must be `available` or partially `allocated` (still has stock).
- `quantity_to_allocate` must be ≥ 1 and ≤ `available_quantity`.
- `available_quantity` is decremented by the allocated amount.
- When `available_quantity` reaches 0 the `status` transitions to `allocated`.
- `assigned_disaster` is set to the provided `disaster_id`.

Requires: **Government** or **NGO** role.
    """,
)
async def allocate_resource(
    resource_id: Annotated[UUID, Path(description="UUID of the resource to allocate.")],
    payload: Annotated[
        AllocateRequest,
        Body(
            openapi_examples={
                "allocate_food": {
                    "summary": "Allocate 500 food units to a disaster",
                    "value": {
                        "disaster_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "quantity_to_allocate": 500,
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrNGO,
) -> Any:
    resource = resource_service.allocate_resource(
        db=db,
        resource_id=resource_id,
        disaster_id=payload.disaster_id,
        quantity_to_allocate=payload.quantity_to_allocate,
    )
    return success_response(
        data=_serialize(resource),
        message=(
            f"Allocated {payload.quantity_to_allocate} unit(s) to "
            f"disaster '{payload.disaster_id}'. "
            f"Remaining available: {resource.available_quantity}."
        ),
    )


# ===========================================================================
# GOVERNMENT + NGO + VOLUNTEER — read-only operations
# ===========================================================================


@router.get(
    "/",
    summary="List all resources",
    description="""
Retrieve a paginated, filtered, and searchable list of all active resource records.

### Filtering
- **resource_type**: Substring match (e.g. `food`, `water`, `medicine`)
- **status**: Exact match (`available` | `allocated` | `in_transit` | `consumed`)
- **location**: Substring match on storage location
- **disaster_id**: Returns only resources assigned to this disaster UUID

### Search
- **search**: Keyword search across `resource_type` and `location`

### Sorting
- **sort_by**: `newest` (default) | `oldest` | `type` | `status` | `quantity`

### Pagination
- **page** + **page_size** (1-indexed, max page_size = 100)

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def list_resources(
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireReadAccess,
    # Filters
    resource_type: Optional[str] = Query(
        None,
        description="Filter by resource category (substring match).",
    ),
    filter_status: Optional[ResourceStatus] = Query(
        None,
        alias="status",
        description="Filter by status: available | allocated | in_transit | consumed.",
    ),
    location: Optional[str] = Query(
        None,
        description="Filter by storage location (substring match).",
    ),
    disaster_id: Optional[UUID] = Query(
        None,
        description="Filter to resources assigned to this disaster UUID.",
    ),
    # Search
    search: Optional[str] = Query(
        None,
        description="Keyword search across resource_type and location.",
    ),
    # Sort
    sort_by: str = Query("newest", description=_SORT_BY_DESCRIPTION),
    # Pagination
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
) -> Any:
    resources, total = resource_service.list_resources(
        db=db,
        resource_type=resource_type,
        filter_status=filter_status,
        location=location,
        disaster_id=disaster_id,
        search=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(resources),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(resources)} of {total} resource(s).",
    )


@router.get(
    "/allocation-suggestions",
    summary="Suggest how to distribute unassigned resources across active disasters",
    description="""
Compute suggested allocations for every currently **unassigned, available**
resource depot row, splitting each row's stock across active disasters by
a weighted-proportional (largest-remainder) apportionment of their need
scores — see `/disasters/need-scores` for how need is computed.

Every unit of unassigned stock is accounted for in the suggestions (nothing
is left unaccounted), and higher-need disasters receive a proportionally
larger share. This endpoint only computes suggestions — nothing is written
to the database. Apply a suggestion by calling
`PATCH /resources/{resource_id}/allocate` with the suggested quantity and
disaster_id.

Requires: **Government** or **NGO** role (same as manual allocation).
    """,
)
async def get_allocation_suggestions(
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrNGO,
) -> Any:
    suggestions: list[AllocationSuggestionItem] = allocation_service.suggest_allocations(db)
    return success_response(
        data=[item.model_dump(mode="json") for item in suggestions],
        message=f"Computed {len(suggestions)} allocation suggestion(s).",
    )


@router.get(
    "/{resource_id}",
    summary="Get a resource by ID",
    description="""
Retrieve the full details of a specific resource record by its UUID.

Returns **HTTP 404** if the resource does not exist or has been soft-deleted.

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def get_resource(
    resource_id: Annotated[UUID, Path(description="UUID of the resource to retrieve.")],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireReadAccess,
) -> Any:
    resource = resource_service.get_resource_by_id(db=db, resource_id=resource_id)
    return success_response(
        data=_serialize(resource),
        message="Resource retrieved successfully.",
    )
