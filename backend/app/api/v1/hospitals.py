"""
app/api/v1/hospitals.py

Hospital Management router — complete production implementation.

Prefix : /api/v1/hospitals
Tags   : Hospitals

Endpoint map
------------
POST  /                            → Register a new hospital          (Government)
GET   /                            → List hospitals with filters       (Gov + Hospital + NGO + Volunteer)
GET   /{hospital_id}               → Retrieve a hospital by UUID       (Gov + Hospital + NGO + Volunteer)
PUT   /{hospital_id}               → Full/partial update               (Gov + Hospital own record)
DELETE /{hospital_id}              → Soft-delete a hospital            (Government)
PATCH /{hospital_id}/availability  → Update capacity fields            (Gov + Hospital own record)

Permissions
-----------
Government : Full CRUD + availability update
Hospital   : Read all + update own record + availability own record
NGO        : Read only (list + get)
Volunteer  : Read only (list + get)
Citizen    : No access
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
from app.schemas.hospital import (
    AvailabilityUpdate,
    HospitalCreate,
    HospitalResponse,
    HospitalUpdate,
)
from app.services import hospital_service
from app.utils.constants import (
    API_V1_TAG_HOSPITALS,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/hospitals",
    tags=[API_V1_TAG_HOSPITALS],
)

# ---------------------------------------------------------------------------
# Multi-role permission aliases (built inline — no modifications to other files)
# ---------------------------------------------------------------------------

# Government + Hospital — write to own record
_RequireGovOrHospital = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.HOSPITAL)),
]

# Government + Hospital + NGO + Volunteer — read access
_RequireReadAccess = Annotated[
    User,
    Depends(
        require_role(
            RoleEnum.GOVERNMENT,
            RoleEnum.HOSPITAL,
            RoleEnum.NGO,
            RoleEnum.VOLUNTEER,
        )
    ),
]


# ---------------------------------------------------------------------------
# Private serialisation helpers
# ---------------------------------------------------------------------------


def _serialize(hospital: Any) -> dict[str, Any]:
    """Convert a Hospital ORM instance to a JSON-serialisable dict."""
    return HospitalResponse.model_validate(hospital).model_dump(mode="json")


def _serialize_list(hospitals: list[Any]) -> list[dict[str, Any]]:
    """Bulk serialise a list of Hospital ORM instances."""
    return [_serialize(h) for h in hospitals]


# ---------------------------------------------------------------------------
# Shared query parameter description
# ---------------------------------------------------------------------------
_SORT_BY_DESCRIPTION = (
    "Sort field. Options: newest (default) | oldest | name | beds | icu."
)


# ===========================================================================
# GOVERNMENT-ONLY — administrative write operations
# ===========================================================================


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new hospital",
    description="""
Register a medical facility in the ResQMesh disaster relief network.

### Capacity fields
All integer capacity fields default to **0** and must be ≥ 0:
- `available_beds` — general ward beds available for admission
- `icu_beds` — intensive care unit beds
- `ventilators` — mechanical ventilators
- `ambulances` — operational ambulances
- `blood_units` — blood units available across all types
- `oxygen_units` — oxygen cylinders / units

### Uniqueness
Hospital names must be unique (case-insensitive). Registration of a
duplicate name returns **HTTP 409**.

Requires: **Government** role.
    """,
)
async def create_hospital(
    data: Annotated[
        HospitalCreate,
        Body(
            openapi_examples={
                "full_registration": {
                    "summary": "Full hospital registration",
                    "value": {
                        "hospital_name": "Government General Hospital Chennai",
                        "latitude": 13.0604,
                        "longitude": 80.2496,
                        "available_beds": 120,
                        "icu_beds": 18,
                        "ventilators": 10,
                        "ambulances": 6,
                        "blood_units": 80,
                        "oxygen_units": 200,
                        "contact_number": "+914428190000",
                    },
                },
                "minimal_registration": {
                    "summary": "Minimal registration (name only)",
                    "value": {
                        "hospital_name": "Coimbatore District Hospital",
                        "contact_number": "+914222300123",
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    hospital = hospital_service.create_hospital(db=db, data=data)
    return success_response(
        data=_serialize(hospital),
        message="Hospital registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.delete(
    "/{hospital_id}",
    summary="Delete a hospital record",
    description="""
Soft-delete a hospital record (`is_deleted = true`).

The record is retained in the database for audit purposes and will
no longer appear in any list or retrieval results.

Requires: **Government** role.
    """,
)
async def delete_hospital(
    hospital_id: Annotated[
        UUID, Path(description="UUID of the hospital to delete.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    hospital_service.delete_hospital(db=db, hospital_id=hospital_id)
    return success_response(message="Hospital deleted successfully.")


# ===========================================================================
# GOVERNMENT + HOSPITAL — update operations (Hospital users: own record only)
# ===========================================================================


@router.put(
    "/{hospital_id}",
    summary="Update a hospital record",
    description="""
Perform a partial update on an existing hospital record.

Only fields included in the request body are modified — omitted fields
retain their current values.

### Ownership rule for Hospital users
Hospital-role users may only update their **own** facility record.
Ownership is determined by matching `organization_name` (set at user
registration) against the `hospital_name` of the target record
(case-insensitive). Attempting to update another hospital returns
**HTTP 403**.

Requires: **Government** or **Hospital** role.
    """,
)
async def update_hospital(
    hospital_id: Annotated[
        UUID, Path(description="UUID of the hospital to update.")
    ],
    data: HospitalUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrHospital,
) -> Any:
    hospital = hospital_service.update_hospital(
        db=db,
        hospital_id=hospital_id,
        data=data,
        current_user=current_user,
    )
    return success_response(
        data=_serialize(hospital),
        message="Hospital updated successfully.",
    )


@router.patch(
    "/{hospital_id}/availability",
    summary="Update hospital capacity and availability",
    description="""
Targeted real-time update of one or more capacity fields.

Use this endpoint to report current bed counts, equipment levels,
and supply availability without modifying other hospital details.

### Updatable fields
- `available_beds` — general ward beds
- `icu_beds` — intensive care beds
- `ventilators` — mechanical ventilators
- `ambulances` — operational ambulances
- `blood_units` — blood units
- `oxygen_units` — oxygen cylinders/units

At least one field must be provided. All values must be ≥ 0.

### Ownership rule for Hospital users
Hospital-role users may only update their **own** facility record
(matched by `organization_name`).

Requires: **Government** or **Hospital** role.
    """,
)
async def update_availability(
    hospital_id: Annotated[
        UUID, Path(description="UUID of the hospital to update.")
    ],
    payload: Annotated[
        AvailabilityUpdate,
        Body(
            openapi_examples={
                "beds_and_icu": {
                    "summary": "Report updated bed and ICU counts",
                    "value": {
                        "available_beds": 45,
                        "icu_beds": 8,
                    },
                },
                "full_capacity_update": {
                    "summary": "Full capacity report",
                    "value": {
                        "available_beds": 90,
                        "icu_beds": 12,
                        "ventilators": 7,
                        "ambulances": 4,
                        "blood_units": 60,
                        "oxygen_units": 150,
                    },
                },
                "supply_restock": {
                    "summary": "Blood and oxygen restock only",
                    "value": {
                        "blood_units": 120,
                        "oxygen_units": 300,
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrHospital,
) -> Any:
    hospital = hospital_service.update_availability(
        db=db,
        hospital_id=hospital_id,
        data=payload,
        current_user=current_user,
    )
    return success_response(
        data=_serialize(hospital),
        message="Hospital availability updated successfully.",
    )


# ===========================================================================
# READ-ONLY — Government + Hospital + NGO + Volunteer
# ===========================================================================


@router.get(
    "/",
    summary="List all hospitals",
    description="""
Retrieve a paginated, filtered, and searchable list of all registered hospitals.

### Search
- **search**: Keyword match across `hospital_name` and `contact_number`

### Availability filters
- **has_beds**: `true` → only hospitals with `available_beds > 0`
- **has_icu**: `true` → only hospitals with `icu_beds > 0`
- **has_ventilators**: `true` → only hospitals with `ventilators > 0`
- **has_ambulances**: `true` → only hospitals with `ambulances > 0`
- **min_beds**: Minimum number of `available_beds` required
- **min_icu**: Minimum number of `icu_beds` required

### Sorting
- **sort_by**: `newest` (default) | `oldest` | `name` | `beds` | `icu`

### Pagination
- **page** + **page_size** (1-indexed, max page_size = 100)

Requires: **Government**, **Hospital**, **NGO**, or **Volunteer** role.
    """,
)
async def list_hospitals(
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireReadAccess,
    # Search
    search: Optional[str] = Query(
        None,
        description="Keyword search across hospital_name and contact_number.",
    ),
    # Availability filters
    has_beds: Optional[bool] = Query(
        None,
        description="When true, only return hospitals with available_beds > 0.",
    ),
    has_icu: Optional[bool] = Query(
        None,
        description="When true, only return hospitals with icu_beds > 0.",
    ),
    has_ventilators: Optional[bool] = Query(
        None,
        description="When true, only return hospitals with ventilators > 0.",
    ),
    has_ambulances: Optional[bool] = Query(
        None,
        description="When true, only return hospitals with ambulances > 0.",
    ),
    min_beds: Optional[int] = Query(
        None,
        ge=0,
        description="Minimum number of available_beds required.",
    ),
    min_icu: Optional[int] = Query(
        None,
        ge=0,
        description="Minimum number of icu_beds required.",
    ),
    # Sorting
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
    hospitals, total = hospital_service.list_hospitals(
        db=db,
        search=search,
        has_beds=has_beds,
        has_icu=has_icu,
        has_ventilators=has_ventilators,
        has_ambulances=has_ambulances,
        min_beds=min_beds,
        min_icu=min_icu,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(hospitals),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(hospitals)} of {total} hospital(s).",
    )


@router.get(
    "/{hospital_id}",
    summary="Get a hospital by ID",
    description="""
Retrieve the full details of a specific hospital record by its UUID.

Returns **HTTP 404** if the hospital does not exist or has been soft-deleted.

Requires: **Government**, **Hospital**, **NGO**, or **Volunteer** role.
    """,
)
async def get_hospital(
    hospital_id: Annotated[
        UUID, Path(description="UUID of the hospital to retrieve.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireReadAccess,
) -> Any:
    hospital = hospital_service.get_hospital_by_id(db=db, hospital_id=hospital_id)
    return success_response(
        data=_serialize(hospital),
        message="Hospital retrieved successfully.",
    )
