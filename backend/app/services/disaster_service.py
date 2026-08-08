"""
app/services/disaster_service.py

Business logic for the Disaster module.

Responsibilities
----------------
- CRUD operations (create, read, update, soft-delete)
- List with full filtering, pagination, and search
- Status transitions (verify → resource_allocated → rescue_ongoing → resolved)
- Severity updates
- No router logic in this layer

All queries use SQLAlchemy 2.0 select() API.
Soft-delete is enforced via is_deleted filter on every read.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.disaster import Disaster
from app.models.enums import DisasterSeverity, DisasterStatus
from app.schemas.disaster import DisasterCreate, DisasterUpdate


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_404(db: Session, disaster_id: UUID) -> Disaster:
    """Load a non-deleted Disaster by ID, or raise HTTP 404."""
    stmt = (
        select(Disaster)
        .where(Disaster.id == disaster_id)
        .where(Disaster.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disaster with id '{disaster_id}' not found.",
        )
    return obj


def _apply_filters(
    stmt,
    severity: Optional[DisasterSeverity],
    disaster_status: Optional[DisasterStatus],
    district: Optional[str],
    state: Optional[str],
    disaster_type: Optional[str],
    search: Optional[str],
    from_date: Optional[datetime],
    to_date: Optional[datetime],
):
    """Apply all optional query filters to a select statement."""
    if severity:
        stmt = stmt.where(Disaster.severity == severity)
    if disaster_status:
        stmt = stmt.where(Disaster.status == disaster_status)
    if district:
        stmt = stmt.where(Disaster.district.ilike(f"%{district}%"))
    if state:
        stmt = stmt.where(Disaster.state.ilike(f"%{state}%"))
    if disaster_type:
        stmt = stmt.where(Disaster.disaster_type.ilike(f"%{disaster_type}%"))
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Disaster.title.ilike(term),
                Disaster.description.ilike(term),
                Disaster.district.ilike(term),
            )
        )
    if from_date:
        stmt = stmt.where(Disaster.created_at >= from_date)
    if to_date:
        stmt = stmt.where(Disaster.created_at <= to_date)
    return stmt


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_disaster(
    db: Session,
    data: DisasterCreate,
    reported_by: UUID,
) -> Disaster:
    """
    Create and persist a new Disaster record.

    Args:
        db:           Active database session.
        data:         Validated create payload.
        reported_by:  UUID of the authenticated user submitting the record.

    Returns:
        The newly created Disaster ORM instance.
    """
    disaster = Disaster(
        title=data.title,
        description=data.description,
        disaster_type=data.disaster_type,
        severity=data.severity,
        status=data.status if data.status else DisasterStatus.REPORTED,
        latitude=data.latitude,
        longitude=data.longitude,
        district=data.district,
        state=data.state,
        country=data.country or "India",
        reported_by=reported_by,
    )
    try:
        db.add(disaster)
        db.commit()
        db.refresh(disaster)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create disaster record.",
        ) from exc
    return disaster


def get_disaster_by_id(db: Session, disaster_id: UUID) -> Disaster:
    """Retrieve a single non-deleted Disaster by UUID."""
    return _get_or_404(db, disaster_id)


def list_disasters(
    db: Session,
    severity: Optional[DisasterSeverity] = None,
    disaster_status: Optional[DisasterStatus] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    disaster_type: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Disaster], int]:
    """
    Return a paginated, filtered, sorted list of disasters.

    Args:
        sort_by:    Field to sort on. Accepts: created_at | title | severity |
                    status | oldest (alias for created_at asc).
        sort_order: 'asc' or 'desc'. Ignored when sort_by='oldest'.

    Returns:
        (list of Disaster ORM objects, total matching count)
    """
    base = (
        select(Disaster)
        .where(Disaster.is_deleted.is_(False))
    )
    base = _apply_filters(
        base, severity, disaster_status, district, state,
        disaster_type, search, from_date, to_date,
    )

    # Total count
    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    # Sorting resolution
    _sort_map = {
        "created_at": Disaster.created_at,
        "newest": Disaster.created_at,
        "oldest": Disaster.created_at,
        "title": Disaster.title,
        "severity": Disaster.severity,
        "status": Disaster.status,
    }
    sort_col = _sort_map.get(sort_by, Disaster.created_at)

    # 'oldest' is always ascending regardless of sort_order
    if sort_by == "oldest" or sort_order.lower() == "asc":
        order_expr = sort_col.asc()
    else:
        order_expr = sort_col.desc()

    # Paginated results
    items_stmt = (
        base
        .order_by(order_expr)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    disasters = list(db.execute(items_stmt).scalars().all())

    return disasters, total


def update_disaster(
    db: Session,
    disaster_id: UUID,
    data: DisasterUpdate,
) -> Disaster:
    """
    Partially update a Disaster record.

    Only fields explicitly included in the request body are modified.
    """
    disaster = _get_or_404(db, disaster_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(disaster, field, value)
    try:
        db.commit()
        db.refresh(disaster)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update disaster record.",
        ) from exc
    return disaster


def delete_disaster(db: Session, disaster_id: UUID) -> None:
    """Soft-delete a Disaster by setting is_deleted = True."""
    disaster = _get_or_404(db, disaster_id)
    disaster.is_deleted = True
    db.commit()


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

def verify_disaster(db: Session, disaster_id: UUID) -> Disaster:
    """
    Mark a REPORTED disaster as VERIFIED.

    Only disasters currently in REPORTED status can be verified.
    """
    disaster = _get_or_404(db, disaster_id)
    if disaster.status != DisasterStatus.REPORTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot verify disaster with current status '{disaster.status.value}'. "
                "Only 'reported' disasters can be verified."
            ),
        )
    disaster.status = DisasterStatus.VERIFIED
    db.commit()
    db.refresh(disaster)
    return disaster


def update_severity(
    db: Session,
    disaster_id: UUID,
    severity: DisasterSeverity,
) -> Disaster:
    """Update the severity level of an existing disaster."""
    disaster = _get_or_404(db, disaster_id)
    disaster.severity = severity
    db.commit()
    db.refresh(disaster)
    return disaster


def update_status(
    db: Session,
    disaster_id: UUID,
    new_status: DisasterStatus,
) -> Disaster:
    """
    Update the lifecycle status of an existing disaster.

    No transition validation — Government users are trusted to set
    the correct status. Validation can be added in a future hardening phase.
    """
    disaster = _get_or_404(db, disaster_id)
    disaster.status = new_status
    db.commit()
    db.refresh(disaster)
    return disaster
