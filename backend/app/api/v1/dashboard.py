"""
app/api/v1/dashboard.py

Dashboard analytics router — complete production implementation.

Prefix : /api/v1/dashboard
Tags   : Dashboard

Endpoint map
------------
GET /summary     → Platform-wide KPI counters
GET /statistics  → Per-enum breakdown counts (charts/graphs)
GET /disasters   → Recent active disaster snapshot
GET /resources   → Resource inventory aggregation
GET /hospitals   → Hospital capacity fleet summary

All endpoints require Government role.
All business logic is inside dashboard_service.py.
This router only calls service methods and wraps results in success_response().
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment
from app.database.session import get_db
from app.services import dashboard_service
from app.utils.constants import API_V1_TAG_DASHBOARD
from app.utils.response import success_response

router = APIRouter(
    prefix="/dashboard",
    tags=[API_V1_TAG_DASHBOARD],
)


@router.get(
    "/summary",
    summary="Platform-wide KPI summary",
    description="""
Return a single aggregated snapshot of the entire ResQMesh platform,
covering all major entities in one response.

### Sections returned
- **disasters** — total, active, resolved counts
- **emergency_reports** — total, verified, unverified counts
- **resources** — total, available, allocated counts
- **shelters** — total shelters, capacity, occupancy, available spots
- **hospitals** — total hospitals, available beds, ICU beds
- **assignments** — total, currently active (in_progress)
- **users** — total active users, total volunteers
- **notifications** — unread count

Requires: **Government** role.
    """,
)
async def get_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    data = dashboard_service.get_summary(db=db)
    return success_response(
        data=data,
        message="Platform summary retrieved successfully.",
    )


@router.get(
    "/statistics",
    summary="Aggregated breakdown statistics",
    description="""
Return per-enum value breakdown counts across core entities.
Designed for populating bar charts, pie charts, and status grids.

### Sections returned
- **disasters.by_status** — count per DisasterStatus value
- **disasters.by_severity** — count per DisasterSeverity value
- **resources.by_status** — count per ResourceStatus value
- **resources.by_type** — count per resource type (top 10)
- **assignments.by_status** — count per AssignmentStatus value
- **users.by_role** — count of active users per RoleEnum value

Requires: **Government** role.
    """,
)
async def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    data = dashboard_service.get_statistics(db=db)
    return success_response(
        data=data,
        message="Platform statistics retrieved successfully.",
    )


@router.get(
    "/disasters",
    summary="Recent active disasters snapshot",
    description="""
Return the most recent active (non-resolved) disaster events.

### Fields per record
`id`, `title`, `disaster_type`, `severity`, `status`, `location`, `created_at`

### Query parameters
- **limit** — maximum number of records to return (1–50, default 10)

Requires: **Government** role.
    """,
)
async def get_disasters(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of disaster records to return (1–50).",
    ),
) -> Any:
    data = dashboard_service.get_disasters_snapshot(db=db, limit=limit)
    return success_response(
        data=data,
        message=f"Retrieved {len(data)} active disaster(s).",
    )


@router.get(
    "/resources",
    summary="Resource inventory aggregation",
    description="""
Return aggregated inventory totals across all resource records,
broken down by resource type.

### Top-level fields
- `total_records` — number of resource entries
- `total_quantity` — sum of all `quantity` values
- `available_quantity` — sum of all `available_quantity` values

### Per-type breakdown (`by_type`)
Each entry includes `resource_type`, `record_count`,
`total_quantity`, and `available_quantity`.

Requires: **Government** role.
    """,
)
async def get_resources(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    data = dashboard_service.get_resources_snapshot(db=db)
    return success_response(
        data=data,
        message="Resource inventory summary retrieved successfully.",
    )


@router.get(
    "/hospitals",
    summary="Hospital capacity fleet summary",
    description="""
Return platform-wide hospital capacity totals plus a ranked list of
hospitals ordered by available beds (descending).

### Top-level totals
`total_hospitals`, `total_available_beds`, `total_icu_beds`,
`total_ventilators`, `total_ambulances`, `total_blood_units`,
`total_oxygen_units`

### Per-hospital list fields
`id`, `hospital_name`, `available_beds`, `icu_beds`, `ventilators`,
`ambulances`, `blood_units`, `oxygen_units`, `contact_number`,
`latitude`, `longitude`

### Query parameters
- **limit** — maximum number of hospital records to return (1–50, default 10)

Requires: **Government** role.
    """,
)
async def get_hospitals(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of hospital records to return (1–50).",
    ),
) -> Any:
    data = dashboard_service.get_hospitals_snapshot(db=db, limit=limit)
    return success_response(
        data=data,
        message="Hospital capacity summary retrieved successfully.",
    )
