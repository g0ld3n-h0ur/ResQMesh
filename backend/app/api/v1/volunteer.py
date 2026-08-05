"""
app/api/v1/volunteer.py

Assignment Management router.

The volunteer.py file hosts the /assignments router because the
app/main.py already registers volunteer.router under /api/v1.
Changing the prefix here to /assignments delivers all endpoints
at /api/v1/assignments as specified.

Prefix : /api/v1/assignments
Tags   : Volunteer

Endpoint map
------------
POST  /                        → Create a new assignment            (Gov + NGO)
GET   /                        → List assignments                   (Gov + NGO + Volunteer)
GET   /{assignment_id}         → Get assignment by UUID             (Gov + NGO + Volunteer)
PUT   /{assignment_id}         → Update assignment record           (Gov + NGO)
DELETE /{assignment_id}        → Soft-delete an assignment          (Government)
PATCH /{assignment_id}/status  → Transition assignment status       (Gov + NGO + Volunteer)

Permissions
-----------
Government  : Full CRUD + status transitions
NGO         : Create + read + update + status transitions
Volunteer   : Read own assignments + update own status only
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import RequireGovernment, require_role
from app.database.session import get_db
from app.dependencies.auth import CurrentUser
from app.models.enums import AssignmentStatus, RoleEnum
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate
from app.services import assignment_service
from app.utils.constants import (
    API_V1_TAG_VOLUNTEER,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(
    prefix="/assignments",
    tags=[API_V1_TAG_VOLUNTEER],
)

# ---------------------------------------------------------------------------
# Multi-role permission aliases
# ---------------------------------------------------------------------------

# Government + NGO — create and manage assignments
_RequireGovOrNGO = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO)),
]

# Government + NGO + Volunteer — read + status ops
_RequireOpsAccess = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO, RoleEnum.VOLUNTEER)),
]


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _serialize(assignment: Any) -> dict[str, Any]:
    return AssignmentResponse.model_validate(assignment).model_dump(mode="json")


def _serialize_list(assignments: list[Any]) -> list[dict[str, Any]]:
    return [_serialize(a) for a in assignments]


_SORT_BY_DESCRIPTION = "Sort field. Options: newest (default) | oldest | status."


# ===========================================================================
# GOVERNMENT ONLY — administrative delete
# ===========================================================================


@router.delete(
    "/{assignment_id}",
    summary="Delete an assignment",
    description="""
Soft-delete an assignment record (`is_deleted = true`).

**Constraint**: assignments with status `in_progress` cannot be deleted.
Cancel the assignment first using `PATCH /{id}/status`.

Requires: **Government** role.
    """,
)
async def delete_assignment(
    assignment_id: Annotated[
        UUID, Path(description="UUID of the assignment to delete.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireGovernment,
) -> Any:
    assignment_service.delete_assignment(db=db, assignment_id=assignment_id)
    return success_response(message="Assignment deleted successfully.")


# ===========================================================================
# GOVERNMENT + NGO — create and update
# ===========================================================================


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assignment",
    description="""
Create a new assignment linking response actors to a disaster event.

### Required
- `disaster_id` — the disaster event this assignment belongs to

### Optional assignees (at least one recommended)
- `volunteer_id` — UUID of a volunteer user
- `ngo_id`       — UUID of an NGO user
- `hospital_id`  — UUID of a hospital
- `resource_id`  — UUID of a relief resource

All referenced UUIDs are validated against live records. Default status
is `pending`.

Requires: **Government** or **NGO** role.
    """,
)
async def create_assignment(
    data: Annotated[
        AssignmentCreate,
        Body(
            openapi_examples={
                "volunteer_assignment": {
                    "summary": "Assign a volunteer to a disaster",
                    "value": {
                        "disaster_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "volunteer_id": "4ba85f64-5717-4562-b3fc-2c963f66afa7",
                        "status": "pending",
                    },
                },
                "resource_assignment": {
                    "summary": "Assign a resource to a disaster",
                    "value": {
                        "disaster_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "resource_id": "5ca85f64-5717-4562-b3fc-2c963f66afa8",
                        "status": "pending",
                    },
                },
                "full_assignment": {
                    "summary": "Full multi-entity assignment",
                    "value": {
                        "disaster_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "volunteer_id": "4ba85f64-5717-4562-b3fc-2c963f66afa7",
                        "ngo_id": "6da85f64-5717-4562-b3fc-2c963f66afa9",
                        "hospital_id": "7ea85f64-5717-4562-b3fc-2c963f66afb0",
                        "resource_id": "5ca85f64-5717-4562-b3fc-2c963f66afa8",
                        "status": "pending",
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrNGO,
) -> Any:
    assignment = assignment_service.create_assignment(db=db, data=data)
    return success_response(
        data=_serialize(assignment),
        message="Assignment created successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/{assignment_id}",
    summary="Update an assignment record",
    description="""
Partially update an existing assignment record.

Only fields included in the request body are modified. All referenced
FK UUIDs are validated against live records before updating.

Volunteers are not permitted to call this endpoint (use `PATCH /{id}/status`
for status-only updates).

Requires: **Government** or **NGO** role.
    """,
)
async def update_assignment(
    assignment_id: Annotated[
        UUID, Path(description="UUID of the assignment to update.")
    ],
    data: AssignmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrNGO,
) -> Any:
    assignment = assignment_service.update_assignment(
        db=db,
        assignment_id=assignment_id,
        data=data,
        current_user=current_user,
    )
    return success_response(
        data=_serialize(assignment),
        message="Assignment updated successfully.",
    )


# ===========================================================================
# GOVERNMENT + NGO + VOLUNTEER — read + status operations
# ===========================================================================


@router.patch(
    "/{assignment_id}/status",
    summary="Update assignment status",
    description="""
Transition an assignment to a new lifecycle status.

### Allowed transitions
| Current status | Allowed next statuses |
|---|---|
| `pending` | `in_progress`, `cancelled` |
| `in_progress` | `completed`, `cancelled` |
| `completed` | *(terminal — no transitions)* |
| `cancelled` | *(terminal — no transitions)* |

### Volunteer restrictions
Volunteers can only update **their own** assignments and may only
transition to `in_progress` or `completed`.

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def update_assignment_status(
    assignment_id: Annotated[
        UUID, Path(description="UUID of the assignment.")
    ],
    payload: Annotated[
        dict,
        Body(
            openapi_examples={
                "start_work": {
                    "summary": "Start the assignment",
                    "value": {"status": "in_progress"},
                },
                "complete": {
                    "summary": "Mark as completed",
                    "value": {"status": "completed"},
                },
                "cancel": {
                    "summary": "Cancel the assignment",
                    "value": {"status": "cancelled"},
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireOpsAccess,
) -> Any:
    new_status_str: str = payload.get("status", "")
    try:
        new_status = AssignmentStatus(new_status_str)
    except ValueError:
        valid = [s.value for s in AssignmentStatus]
        from fastapi import HTTPException as _HTTPException
        raise _HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{new_status_str}'. Valid values: {valid}.",
        )

    assignment = assignment_service.update_status(
        db=db,
        assignment_id=assignment_id,
        new_status=new_status,
        current_user=current_user,
    )
    return success_response(
        data=_serialize(assignment),
        message=f"Assignment status updated to '{new_status.value}'.",
    )


@router.get(
    "/",
    summary="List all assignments",
    description="""
Retrieve a paginated, filtered list of assignment records.

### Scope
- **Volunteer**: automatically scoped to their own assignments only
  (the `volunteer_id` filter is ignored and replaced with their own UUID).
- **Government / NGO**: full visibility across all assignments.

### Filters
- **disaster_id**: Only assignments for this disaster
- **volunteer_id**: Only assignments for this volunteer (Gov/NGO only)
- **ngo_id**: Only assignments for this NGO (Gov/NGO only)
- **status**: `pending` | `in_progress` | `completed` | `cancelled`

### Sorting
- **sort_by**: `newest` (default) | `oldest` | `status`

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def list_assignments(
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireOpsAccess,
    disaster_id: Optional[UUID] = Query(
        None, description="Filter by disaster UUID."
    ),
    volunteer_id: Optional[UUID] = Query(
        None, description="Filter by volunteer UUID (Government/NGO only)."
    ),
    ngo_id: Optional[UUID] = Query(
        None, description="Filter by NGO UUID (Government/NGO only)."
    ),
    filter_status: Optional[AssignmentStatus] = Query(
        None,
        alias="status",
        description="Filter by status: pending | in_progress | completed | cancelled.",
    ),
    sort_by: str = Query("newest", description=_SORT_BY_DESCRIPTION),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Results per page (max {MAX_PAGE_SIZE}).",
    ),
) -> Any:
    assignments, total = assignment_service.list_assignments(
        db=db,
        current_user=current_user,
        disaster_id=disaster_id,
        volunteer_id=volunteer_id,
        ngo_id=ngo_id,
        filter_status=filter_status,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return paginated_response(
        data=_serialize_list(assignments),
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(assignments)} of {total} assignment(s).",
    )


@router.get(
    "/{assignment_id}",
    summary="Get an assignment by ID",
    description="""
Retrieve the full details of a specific assignment by UUID.

Volunteers can only retrieve assignments where they are the assigned
volunteer. All other roles see any assignment.

Returns **HTTP 404** if the assignment does not exist or is soft-deleted.
Returns **HTTP 403** if a volunteer tries to access another's assignment.

Requires: **Government**, **NGO**, or **Volunteer** role.
    """,
)
async def get_assignment(
    assignment_id: Annotated[
        UUID, Path(description="UUID of the assignment to retrieve.")
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireOpsAccess,
) -> Any:
    assignment = assignment_service.get_assignment_by_id(
        db=db, assignment_id=assignment_id, current_user=current_user
    )
    return success_response(
        data=_serialize(assignment),
        message="Assignment retrieved successfully.",
    )
