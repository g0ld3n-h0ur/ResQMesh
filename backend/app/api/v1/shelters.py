"""
app/api/v1/shelters.py

Shelter Management router — complete production implementation.

Prefix : /api/v1/shelters
Tags   : Shelters

Endpoint map
------------
POST  /                          → Register a new shelter          (Government)
GET   /                          → List shelters with filters       (Gov + NGO + Volunteer + Citizen)
GET   /{shelter_id}              → Get a shelter by UUID            (Gov + NGO + Volunteer + Citizen)
PUT   /{shelter_id}              → Update shelter details           (Government)
DELETE /{shelter_id}             → Soft-delete a shelter            (Government)
POST  /{shelter_id}/checkin      → Check evacuees in                (Gov + NGO + Volunteer)
POST  /{shelter_id}/checkout     → Check evacuees out               (Gov + NGO + Volunteer)

Permissions
-----------
Government          : Full CRUD + check-in/out
NGO + Volunteer     : Read + check-in/out
Citizen             : Read only (list + get)
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment, require_role
from app.database.session import get_db
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.shelter import ShelterCreate, ShelterResponse, ShelterUpdate
from app.services import shelter_service
from app.utils.constants import (
    API_V1_TAG_SHELTERS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/shelters",
    tags=[API_V1_TAG_SHELTERS],
)

# ---------------------------------------------------------------------------
# Multi-role permission aliases
# ---------------------------------------------------------------------------

# Gov + NGO + Volunteer — operational write access (check-in/out)
_RequireOpsAccess = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO, RoleEnum.VOLUNTEER)),
]

# Gov + NGO + Volunteer + Citizen — read access
_RequireReadAccess = Annotated[
    User,
    Depends(
        require_role(
            RoleEnum.GOVERNMENT,
            RoleEnum.NGO,
            RoleEnum.VOLUNTEER,
            RoleEnum.CITIZEN,
        )
    ),
]


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _serialize(shelter: Any) -> dict[str, Any]:
    return ShelterResponse.model_validate(shelter).model_dump(mode="json")


def _serialize_list(shelters: list[Any]) -> list[dict[str, Any]]:
    return [_serialize(s) for s in shelters]


_SORT_BY_DESCRIPTION = (
    "Sort field. Options: newest (default) | oldest | name | capacity | available."
)


# ===========================================================================
# GOVERNMENT ONLY — administrative CRUD
# ===========================================================================


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new shelter",
    description="""
Register an emergency shelter facility in the ResQMesh relief network.

- `capacity` — maximum number of evacuees the shelter can house
- `current_occupancy` — evacuees already present at registration time
- `current_occupancy` must not exceed `capacity`

Shelter names must be unique (case-insensitive). Returns **HTTP 409** for duplicates.

Requires: **Government** role.
    """,
)
async def create_shelter(
    data: Annotated[
        ShelterCreate,
        Body(
            openapi_examples={
                "school_shelter": {
                    "summary": "School building repurposed as shelter",
                    "value": {
                        "shelter_name": "Govt Higher Secondary School, Tambaram",
                        "latitude": 12.9249,
                        "longitude": 80.1000,
                        "capacity": 400,
                        "current_occupancy": 0,
                        "contact_number": "+914422391234",
                    },
                },
                "community_hall": {
                    "summary": "Community hall with existing occupants",
                    "value": {
                        "shelter_name": "Anna Nagar Community Hall",
                        "capacity": 250,
                        "current_occupancy": 80,
                        "contact_number": "+914426001234",
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    shelter = shelter_service.create_shelter(db=db, data=data)
    return success_response(
        data=_serialize(shelter),
        message="Shelter registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/{shelter_id}",
    summary="Update a shelter record",
    description="""
Partially update an existing shelter record.

Only fields included in the request body are modified. The service enforces
that `current_occupancy` does not exceed `capacity` after the update.

Requires: **Government** role.
    """,
)
async def update_shelter(
    shelter_id: Annotated[UUID, Path(description="UUID of the shelter to update.")],
    data: ShelterUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    shelter = shelter_service.update_shelter(db=db, shelter_id=shelter_id, data=data)
    return success_response(
        data=_serialize(shelter),
        message="Shelter updated successfully.",
    )


@router.delete(
    "/{shelter_id}",
    summary="Delete a shelter record",
    description="""
Soft-delete a shelter (`is_deleted = true`).

**Constraint**: shelters with active occupants (`current_occupancy > 0`)
cannot be deleted. Check out all evacuees first.

Requires: **Government** role.
    """,
)
async def delete_shelter(
    shelter_id: Annotated[UUID, Path(description="UUID of the shelter to delete.")],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    shelter_service.delete_shelter(db=db, shelter_id=shelter_id)
    return success_response(message="Shelter deleted successfully.")


# ===========================================================================
# GOVERNMENT + NGO + VOLUNTEER — operational write (check-in / check-out)
# ===========================================================================


@router.post(
    "/{shelter_id}/checkin",
    summary="Check evacuees into a shelter",
    description="""
Increment the shelter's `current_occupancy` by `count`.

### Business rules
- `count` must be ≥ 1.
- Resulting occupancy must not exceed `capacity`.
- Returns the updated shelter record with the new occupancy value.

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def checkin_shelter(
    shelter_id: Annotated[UUID, Path(description="UUID of the shelter.")],
    payload: Annotated[
        dict,
        Body(
            openapi_examples={
                "small_group": {
                    "summary": "Check in a family of 4",
                    "value": {"count": 4},
                },
                "large_group": {
                    "summary": "Check in a bus of 45 evacuees",
                    "value": {"count": 45},
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireOpsAccess,
) -> Any:
    count: int = payload.get("count", 0)
    shelter = shelter_service.checkin_shelter(db=db, shelter_id=shelter_id, count=count)
    return success_response(
        data=_serialize(shelter),
        message=(
            f"Checked in {count} evacuee(s). "
            f"Occupancy: {shelter.current_occupancy}/{shelter.capacity}."
        ),
    )


@router.post(
    "/{shelter_id}/checkout",
    summary="Check evacuees out of a shelter",
    description="""
Decrement the shelter's `current_occupancy` by `count`.

### Business rules
- `count` must be ≥ 1.
- Resulting occupancy must not go below 0.
- Returns the updated shelter record with the new occupancy value.

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def checkout_shelter(
    shelter_id: Annotated[UUID, Path(description="UUID of the shelter.")],
    payload: Annotated[
        dict,
        Body(
            openapi_examples={
                "family_checkout": {
                    "summary": "Check out a family of 3",
                    "value": {"count": 3},
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireOpsAccess,
) -> Any:
    count: int = payload.get("count", 0)
    shelter = shelter_service.checkout_shelter(db=db, shelter_id=shelter_id, count=count)
    return success_response(
        data=_serialize(shelter),
        message=(
            f"Checked out {count} evacuee(s). "
            f"Occupancy: {shelter.current_occupancy}/{shelter.capacity}."
        ),
    )


# ===========================================================================
# READ-ONLY — Gov + NGO + Volunteer + Citizen
# ===========================================================================


@router.get(
    "/",
    summary="List all shelters",
    description="""
Retrieve a paginated, filtered, and searchable list of active shelter facilities.

### Search
- **search**: Keyword match across `shelter_name` and `contact_number`

### Filters
- **has_capacity**: `true` → only shelters with available spots remaining
- **min_capacity**: Total `capacity` must be at least N
- **min_available**: Available spots (`capacity − current_occupancy`) must be ≥ N

### Sorting
- **sort_by**: `newest` (default) | `oldest` | `name` | `capacity` | `available`

### Pagination
- **page** + **page_size** (1-indexed, max 100)

Requires: **Government**, **NGO**, **Volunteer**, or **Citizen** role.
    """,
)
async def list_shelters(
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireReadAccess,
    search: Optional[str] = Query(
        None, description="Keyword search across shelter_name and contact_number."
    ),
    has_capacity: Optional[bool] = Query(
        None, description="When true, only shelters with available spots (capacity > occupancy)."
    ),
    min_capacity: Optional[int] = Query(
        None, ge=0, description="Minimum total capacity required."
    ),
    min_available: Optional[int] = Query(
        None, ge=0, description="Minimum available spots (capacity − current_occupancy) required."
    ),
    sort_by: str = Query("newest", description=_SORT_BY_DESCRIPTION),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
) -> Any:
    shelters, total = shelter_service.list_shelters(
        db=db,
        search=search,
        has_capacity=has_capacity,
        min_capacity=min_capacity,
        min_available=min_available,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(shelters),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(shelters)} of {total} shelter(s).",
    )


@router.get(
    "/{shelter_id}",
    summary="Get a shelter by ID",
    description="""
Retrieve the full details of a specific shelter by UUID.

Returns **HTTP 404** if the shelter does not exist or has been soft-deleted.

Requires: **Government**, **NGO**, **Volunteer**, or **Citizen** role.
    """,
)
async def get_shelter(
    shelter_id: Annotated[UUID, Path(description="UUID of the shelter to retrieve.")],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireReadAccess,
) -> Any:
    shelter = shelter_service.get_shelter_by_id(db=db, shelter_id=shelter_id)
    return success_response(
        data=_serialize(shelter),
        message="Shelter retrieved successfully.",
    )
