"""
app/services/assignment_service.py

Business logic for the Assignment module.

Responsibilities
----------------
- Full CRUD (create, read, update, soft-delete)
- Status transition (PATCH /{id}/status)
- List with filtering, sorting, and pagination
- Ownership guard: Volunteers see only their own assigned tasks
- FK existence checks: disaster_id, volunteer_id, ngo_id, hospital_id, resource_id
- Transaction rollback on all write failures

Assignment model facts
----------------------
- disaster_id   : required (NOT NULL FK → disasters)
- volunteer_id  : optional FK → users (role = volunteer)
- ngo_id        : optional FK → users (role = ngo)
- hospital_id   : optional FK → hospitals
- resource_id   : optional FK → resources
- status        : AssignmentStatus enum (pending | in_progress | completed | cancelled)
- assigned_at   : set at creation time

Filtering
---------
- disaster_id   : exact match
- volunteer_id  : exact match
- ngo_id        : exact match
- status        : exact AssignmentStatus match

Sorting
-------
- newest        (created_at DESC, default)
- oldest        (created_at ASC)
- status        (status ASC, then created_at DESC)

All queries use SQLAlchemy 2.0 select() API.
Soft-delete enforced via is_deleted filter on every read.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.disaster import Disaster
from app.models.enums import AssignmentStatus, RoleEnum
from app.models.hospital import Hospital
from app.models.resource import Resource
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate

logger = logging.getLogger("app.services.assignment_service")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, assignment_id: UUID) -> Assignment:
    """Load a non-deleted Assignment by UUID, or raise HTTP 404."""
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id)
        .where(Assignment.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with id '{assignment_id}' not found.",
        )
    return obj


def _assert_disaster_exists(db: Session, disaster_id: UUID) -> None:
    """Raise HTTP 404 if the referenced disaster does not exist."""
    exists = db.execute(
        select(func.count())
        .select_from(Disaster)
        .where(Disaster.id == disaster_id)
        .where(Disaster.is_deleted.is_(False))
    ).scalar_one()
    if exists == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster with id '{disaster_id}' not found.",
        )


def _assert_user_exists(db: Session, user_id: UUID, label: str) -> None:
    """Raise HTTP 404 if the referenced user does not exist."""
    exists = db.execute(
        select(func.count())
        .select_from(User)
        .where(User.id == user_id)
        .where(User.is_deleted.is_(False))
    ).scalar_one()
    if exists == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} user with id '{user_id}' not found.",
        )


def _assert_hospital_exists(db: Session, hospital_id: UUID) -> None:
    """Raise HTTP 404 if the referenced hospital does not exist."""
    exists = db.execute(
        select(func.count())
        .select_from(Hospital)
        .where(Hospital.id == hospital_id)
        .where(Hospital.is_deleted.is_(False))
    ).scalar_one()
    if exists == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with id '{hospital_id}' not found.",
        )


def _assert_resource_exists(db: Session, resource_id: UUID) -> None:
    """Raise HTTP 404 if the referenced resource does not exist."""
    exists = db.execute(
        select(func.count())
        .select_from(Resource)
        .where(Resource.id == resource_id)
        .where(Resource.is_deleted.is_(False))
    ).scalar_one()
    if exists == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id '{resource_id}' not found.",
        )


def _validate_fks(
    db: Session,
    disaster_id: Optional[UUID] = None,
    volunteer_id: Optional[UUID] = None,
    ngo_id: Optional[UUID] = None,
    hospital_id: Optional[UUID] = None,
    resource_id: Optional[UUID] = None,
) -> None:
    """Run all non-null FK existence checks in one call."""
    if disaster_id is not None:
        _assert_disaster_exists(db, disaster_id)
    if volunteer_id is not None:
        _assert_user_exists(db, volunteer_id, "Volunteer")
    if ngo_id is not None:
        _assert_user_exists(db, ngo_id, "NGO")
    if hospital_id is not None:
        _assert_hospital_exists(db, hospital_id)
    if resource_id is not None:
        _assert_resource_exists(db, resource_id)


def _resolve_sort(sort_by: str):
    """Return ORDER BY expression(s) for the requested sort key."""
    _map = {
        "newest": (Assignment.created_at.desc(),),
        "oldest": (Assignment.created_at.asc(),),
        "status": (Assignment.status.asc(), Assignment.created_at.desc()),
    }
    return _map.get(sort_by, (Assignment.created_at.desc(),))


# ---------------------------------------------------------------------------
# Allowed status transitions
# ---------------------------------------------------------------------------
_VALID_TRANSITIONS: dict[AssignmentStatus, set[AssignmentStatus]] = {
    AssignmentStatus.PENDING: {
        AssignmentStatus.IN_PROGRESS,
        AssignmentStatus.CANCELLED,
    },
    AssignmentStatus.IN_PROGRESS: {
        AssignmentStatus.COMPLETED,
        AssignmentStatus.CANCELLED,
    },
    AssignmentStatus.COMPLETED: set(),   # terminal
    AssignmentStatus.CANCELLED: set(),   # terminal
}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_assignment(db: Session, data: AssignmentCreate) -> Assignment:
    """
    Create a new assignment record.

    Validates that all referenced FK entities exist before inserting.
    At least one optional assignee (volunteer_id, ngo_id, hospital_id,
    resource_id) is recommended — this is warned in service logs but not
    enforced as a hard error to maintain schema flexibility.

    Args:
        db:   Active database session.
        data: Validated AssignmentCreate payload.

    Returns:
        The newly created Assignment ORM instance.

    Raises:
        HTTPException 404: Any referenced FK entity not found.
        HTTPException 500: Database write failure.
    """
    _validate_fks(
        db,
        disaster_id=data.disaster_id,
        volunteer_id=data.volunteer_id,
        ngo_id=data.ngo_id,
        hospital_id=data.hospital_id,
        resource_id=data.resource_id,
    )

    if all(
        v is None
        for v in [data.volunteer_id, data.ngo_id, data.hospital_id, data.resource_id]
    ):
        logger.warning(
            "Assignment created for disaster '%s' with no assignee specified.",
            data.disaster_id,
        )

    assignment = Assignment(
        disaster_id=data.disaster_id,
        resource_id=data.resource_id,
        volunteer_id=data.volunteer_id,
        ngo_id=data.ngo_id,
        hospital_id=data.hospital_id,
        status=data.status,
    )
    try:
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create assignment: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create assignment. Please try again.",
        ) from exc

    logger.info(
        "Assignment created: id=%s disaster=%s status=%s",
        assignment.id,
        assignment.disaster_id,
        assignment.status,
    )
    return assignment


def get_assignment_by_id(
    db: Session,
    assignment_id: UUID,
    current_user: User,
) -> Assignment:
    """
    Retrieve a single non-deleted Assignment by UUID.

    Volunteer users can only retrieve assignments where they are the
    volunteer_id. All other roles see any assignment.

    Args:
        db:            Active database session.
        assignment_id: UUID of the assignment to fetch.
        current_user:  Authenticated user performing the request.

    Returns:
        The matching Assignment ORM instance.

    Raises:
        HTTPException 403: Volunteer accessing another's assignment.
        HTTPException 404: Assignment not found or soft-deleted.
    """
    assignment = _get_or_404(db, assignment_id)

    if current_user.role == RoleEnum.VOLUNTEER:
        if assignment.volunteer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Volunteers can only view their own assigned tasks.",
            )

    return assignment


def list_assignments(
    db: Session,
    current_user: User,
    disaster_id: Optional[UUID] = None,
    volunteer_id: Optional[UUID] = None,
    ngo_id: Optional[UUID] = None,
    filter_status: Optional[AssignmentStatus] = None,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Assignment], int]:
    """
    Return a filtered, sorted, and paginated list of assignments.

    Volunteers automatically have their query scoped to assignments where
    volunteer_id == current_user.id, regardless of any filter parameters.

    Args:
        db:           Active database session.
        current_user: Authenticated user performing the request.
        disaster_id:  Filter by disaster UUID.
        volunteer_id: Filter by volunteer UUID.
        ngo_id:       Filter by NGO UUID.
        filter_status: Filter by AssignmentStatus.
        sort_by:      newest | oldest | status.
        page:         1-indexed page number.
        page_size:    Results per page.

    Returns:
        (list of Assignment ORM objects, total matching count)
    """
    base = select(Assignment).where(Assignment.is_deleted.is_(False))

    # Volunteers are always scoped to their own assignments
    if current_user.role == RoleEnum.VOLUNTEER:
        base = base.where(Assignment.volunteer_id == current_user.id)
    else:
        if volunteer_id:
            base = base.where(Assignment.volunteer_id == volunteer_id)
        if ngo_id:
            base = base.where(Assignment.ngo_id == ngo_id)

    if disaster_id:
        base = base.where(Assignment.disaster_id == disaster_id)
    if filter_status:
        base = base.where(Assignment.status == filter_status)

    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    order_exprs = _resolve_sort(sort_by)
    items_stmt = (
        base.order_by(*order_exprs)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    assignments = list(db.execute(items_stmt).scalars().all())
    return assignments, total


def update_assignment(
    db: Session,
    assignment_id: UUID,
    data: AssignmentUpdate,
    current_user: User,
) -> Assignment:
    """
    Partially update an assignment record.

    Validates any newly referenced FK entities. Volunteers cannot update
    assignments.

    Args:
        db:            Active database session.
        assignment_id: UUID of the assignment to update.
        data:          Validated AssignmentUpdate payload.
        current_user:  Authenticated user performing the request.

    Returns:
        The updated Assignment ORM instance.

    Raises:
        HTTPException 403: Volunteer attempting an update.
        HTTPException 404: Assignment or any referenced FK entity not found.
        HTTPException 500: Database write failure.
    """
    if current_user.role == RoleEnum.VOLUNTEER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Volunteers are not permitted to update assignment records.",
        )

    assignment = _get_or_404(db, assignment_id)
    update_data = data.model_dump(exclude_unset=True)

    _validate_fks(
        db,
        volunteer_id=update_data.get("volunteer_id"),
        ngo_id=update_data.get("ngo_id"),
        hospital_id=update_data.get("hospital_id"),
        resource_id=update_data.get("resource_id"),
    )

    for field, value in update_data.items():
        setattr(assignment, field, value)

    try:
        db.commit()
        db.refresh(assignment)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update assignment %s: %s", assignment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assignment. Please try again.",
        ) from exc

    logger.info("Assignment updated: id=%s", assignment.id)
    return assignment


def delete_assignment(
    db: Session,
    assignment_id: UUID,
) -> None:
    """
    Soft-delete an assignment.

    Active (in_progress) assignments cannot be deleted — cancel first.

    Args:
        db:            Active database session.
        assignment_id: UUID of the assignment to soft-delete.

    Raises:
        HTTPException 400: Assignment is currently in_progress.
        HTTPException 404: Assignment not found.
        HTTPException 500: Database write failure.
    """
    assignment = _get_or_404(db, assignment_id)

    if assignment.status == AssignmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete an in-progress assignment '{assignment_id}'. "
                "Cancel it first."
            ),
        )

    assignment.is_deleted = True
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete assignment %s: %s", assignment_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete assignment. Please try again.",
        ) from exc

    logger.info("Assignment soft-deleted: id=%s", assignment_id)


# ---------------------------------------------------------------------------
# Status transition
# ---------------------------------------------------------------------------


def update_status(
    db: Session,
    assignment_id: UUID,
    new_status: AssignmentStatus,
    current_user: User,
) -> Assignment:
    """
    Transition an assignment to a new lifecycle status.

    Enforces allowed transitions:
    - pending     → in_progress | cancelled
    - in_progress → completed   | cancelled
    - completed   → (terminal — no further transitions)
    - cancelled   → (terminal — no further transitions)

    Volunteers may only mark their own assignments as in_progress or completed.

    Args:
        db:            Active database session.
        assignment_id: UUID of the assignment.
        new_status:    Target AssignmentStatus value.
        current_user:  Authenticated user performing the action.

    Returns:
        The updated Assignment ORM instance.

    Raises:
        HTTPException 400: Invalid status transition.
        HTTPException 403: Volunteer acting on another's assignment or
                           attempting a disallowed transition.
        HTTPException 404: Assignment not found.
        HTTPException 500: Database write failure.
    """
    assignment = _get_or_404(db, assignment_id)

    if current_user.role == RoleEnum.VOLUNTEER:
        if assignment.volunteer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Volunteers can only update the status of their own tasks.",
            )
        # Volunteers may only transition to in_progress or completed
        if new_status not in {
            AssignmentStatus.IN_PROGRESS,
            AssignmentStatus.COMPLETED,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Volunteers may only set status to "
                    "'in_progress' or 'completed'."
                ),
            )

    allowed = _VALID_TRANSITIONS.get(assignment.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition assignment from '{assignment.status}' "
                f"to '{new_status}'. "
                f"Allowed transitions: "
                f"{[s.value for s in allowed] or 'none (terminal status)'}."
            ),
        )

    assignment.status = new_status
    try:
        db.commit()
        db.refresh(assignment)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to update status for assignment %s: %s", assignment_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assignment status. Please try again.",
        ) from exc

    logger.info(
        "Assignment status updated: id=%s new_status=%s", assignment.id, new_status
    )
    return assignment
