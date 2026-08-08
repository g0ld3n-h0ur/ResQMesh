"""
app/services/shelter_service.py

Business logic for the Shelter Management module.

Responsibilities
----------------
- Full CRUD (create, read, update, soft-delete)
- Check-in:  increment current_occupancy by N (cannot exceed capacity)
- Check-out: decrement current_occupancy by N (cannot go below 0)
- List with filtering, keyword search, sorting, and pagination
- Duplicate name detection on creation
- Transaction rollback on all write failures

Filtering
---------
- search           : keyword across shelter_name and contact_number
- has_capacity     : only shelters with available_capacity > 0
- min_capacity     : capacity >= N
- min_available    : (capacity - current_occupancy) >= N

Sorting
-------
- newest        (created_at DESC, default)
- oldest        (created_at ASC)
- name          (shelter_name ASC)
- capacity      (capacity DESC)
- available     (available capacity = capacity - current_occupancy, DESC)

All queries use SQLAlchemy 2.0 select() API.
Soft-delete enforced via is_deleted filter on every read.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.shelter import Shelter
from app.schemas.shelter import ShelterCreate, ShelterUpdate

logger = logging.getLogger("app.services.shelter_service")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, shelter_id: UUID) -> Shelter:
    """Load a non-deleted Shelter by UUID, or raise HTTP 404."""
    stmt = (
        select(Shelter)
        .where(Shelter.id == shelter_id)
        .where(Shelter.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelter with id '{shelter_id}' not found.",
        )
    return obj


def _apply_filters(
    stmt,
    search: Optional[str],
    has_capacity: Optional[bool],
    min_capacity: Optional[int],
    min_available: Optional[int],
):
    """Apply all optional query filters to a Shelter select statement."""
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Shelter.shelter_name.ilike(term),
                Shelter.contact_number.ilike(term),
            )
        )
    if has_capacity is True:
        stmt = stmt.where(Shelter.current_occupancy < Shelter.capacity)
    if min_capacity is not None and min_capacity > 0:
        stmt = stmt.where(Shelter.capacity >= min_capacity)
    if min_available is not None and min_available > 0:
        stmt = stmt.where(
            (Shelter.capacity - Shelter.current_occupancy) >= min_available
        )
    return stmt


def _resolve_sort(sort_by: str):
    """Return ORDER BY expression(s) for the requested sort key."""
    _map = {
        "newest": (Shelter.created_at.desc(),),
        "oldest": (Shelter.created_at.asc(),),
        "name": (Shelter.shelter_name.asc(),),
        "capacity": (Shelter.capacity.desc(), Shelter.created_at.desc()),
        "available": (
            (Shelter.capacity - Shelter.current_occupancy).desc(),
            Shelter.created_at.desc(),
        ),
    }
    return _map.get(sort_by, (Shelter.created_at.desc(),))


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_shelter(db: Session, data: ShelterCreate) -> Shelter:
    """
    Register a new emergency shelter facility.

    Args:
        db:   Active database session.
        data: Validated ShelterCreate payload.

    Returns:
        The newly created Shelter ORM instance.

    Raises:
        HTTPException 409: Duplicate shelter name.
        HTTPException 500: Database write failure.
    """
    exists_stmt = (
        select(func.count())
        .select_from(Shelter)
        .where(Shelter.shelter_name.ilike(data.shelter_name))
        .where(Shelter.is_deleted.is_(False))
    )
    if db.execute(exists_stmt).scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A shelter named '{data.shelter_name}' is already registered. "
                "Use a unique shelter name."
            ),
        )

    shelter = Shelter(
        shelter_name=data.shelter_name,
        latitude=data.latitude,
        longitude=data.longitude,
        capacity=data.capacity,
        current_occupancy=data.current_occupancy,
        contact_number=data.contact_number,
    )
    try:
        db.add(shelter)
        db.commit()
        db.refresh(shelter)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create shelter: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register shelter. Please try again.",
        ) from exc

    logger.info("Shelter created: id=%s name=%r", shelter.id, shelter.shelter_name)
    return shelter


def get_shelter_by_id(db: Session, shelter_id: UUID) -> Shelter:
    """
    Retrieve a single non-deleted Shelter by UUID.

    Args:
        db:         Active database session.
        shelter_id: UUID of the shelter to fetch.

    Returns:
        The matching Shelter ORM instance.

    Raises:
        HTTPException 404: Shelter not found or soft-deleted.
    """
    return _get_or_404(db, shelter_id)


def list_shelters(
    db: Session,
    search: Optional[str] = None,
    has_capacity: Optional[bool] = None,
    min_capacity: Optional[int] = None,
    min_available: Optional[int] = None,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Shelter], int]:
    """
    Return a filtered, searched, sorted, and paginated list of shelters.

    Args:
        db:            Active database session.
        search:        Keyword search across shelter_name and contact_number.
        has_capacity:  When True, only shelters with available capacity > 0.
        min_capacity:  Minimum total capacity required.
        min_available: Minimum available spots (capacity - current_occupancy).
        sort_by:       newest | oldest | name | capacity | available.
        page:          1-indexed page number.
        page_size:     Results per page.

    Returns:
        (list of Shelter ORM objects, total matching count)
    """
    base = select(Shelter).where(Shelter.is_deleted.is_(False))
    base = _apply_filters(
        base,
        search=search,
        has_capacity=has_capacity,
        min_capacity=min_capacity,
        min_available=min_available,
    )

    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    order_exprs = _resolve_sort(sort_by)
    items_stmt = (
        base.order_by(*order_exprs)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    shelters = list(db.execute(items_stmt).scalars().all())
    return shelters, total


def update_shelter(
    db: Session,
    shelter_id: UUID,
    data: ShelterUpdate,
) -> Shelter:
    """
    Partially update a Shelter record.

    Only fields explicitly included in the request body are modified.
    Cross-field occupancy guard is applied after merging patch values.

    Args:
        db:         Active database session.
        shelter_id: UUID of the shelter to update.
        data:       Validated ShelterUpdate payload.

    Returns:
        The updated Shelter ORM instance.

    Raises:
        HTTPException 422: current_occupancy would exceed capacity after update.
        HTTPException 404: Shelter not found.
        HTTPException 500: Database write failure.
    """
    shelter = _get_or_404(db, shelter_id)
    update_data = data.model_dump(exclude_unset=True)

    new_capacity = update_data.get("capacity", shelter.capacity)
    new_occupancy = update_data.get("current_occupancy", shelter.current_occupancy)
    if new_occupancy > new_capacity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"current_occupancy ({new_occupancy}) cannot exceed "
                f"capacity ({new_capacity})."
            ),
        )

    for field, value in update_data.items():
        setattr(shelter, field, value)

    try:
        db.commit()
        db.refresh(shelter)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update shelter %s: %s", shelter_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shelter. Please try again.",
        ) from exc

    logger.info("Shelter updated: id=%s", shelter.id)
    return shelter


def delete_shelter(db: Session, shelter_id: UUID) -> None:
    """
    Soft-delete a Shelter by setting is_deleted = True.

    Args:
        db:         Active database session.
        shelter_id: UUID of the shelter to soft-delete.

    Raises:
        HTTPException 400: Shelter still has occupants.
        HTTPException 404: Shelter not found.
        HTTPException 500: Database write failure.
    """
    shelter = _get_or_404(db, shelter_id)

    if shelter.current_occupancy > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete shelter '{shelter_id}' while it has "
                f"{shelter.current_occupancy} occupant(s). "
                "Check out all evacuees before deleting."
            ),
        )

    shelter.is_deleted = True
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete shelter %s: %s", shelter_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete shelter. Please try again.",
        ) from exc

    logger.info("Shelter soft-deleted: id=%s", shelter_id)


# ---------------------------------------------------------------------------
# Occupancy operations
# ---------------------------------------------------------------------------


def checkin_shelter(db: Session, shelter_id: UUID, count: int) -> Shelter:
    """
    Increment current_occupancy by `count` (check citizens in).

    Business rules
    --------------
    - count must be >= 1.
    - Resulting occupancy must not exceed capacity.

    Args:
        db:         Active database session.
        shelter_id: UUID of the shelter.
        count:      Number of evacuees checking in.

    Returns:
        The updated Shelter ORM instance.

    Raises:
        HTTPException 400: Insufficient capacity or invalid count.
        HTTPException 404: Shelter not found.
        HTTPException 500: Database write failure.
    """
    shelter = _get_or_404(db, shelter_id)

    if count <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="count must be a positive integer (>= 1).",
        )

    available = shelter.capacity - shelter.current_occupancy
    if count > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot check in {count} evacuee(s). "
                f"Only {available} spot(s) available "
                f"(capacity={shelter.capacity}, "
                f"current_occupancy={shelter.current_occupancy})."
            ),
        )

    shelter.current_occupancy += count
    try:
        db.commit()
        db.refresh(shelter)
    except Exception as exc:
        db.rollback()
        logger.exception("Check-in failed for shelter %s: %s", shelter_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process check-in. Please try again.",
        ) from exc

    logger.info(
        "Shelter check-in: id=%s count=%s occupancy=%s/%s",
        shelter.id, count, shelter.current_occupancy, shelter.capacity,
    )
    return shelter


def checkout_shelter(db: Session, shelter_id: UUID, count: int) -> Shelter:
    """
    Decrement current_occupancy by `count` (check citizens out).

    Business rules
    --------------
    - count must be >= 1.
    - Resulting occupancy must not go below 0.

    Args:
        db:         Active database session.
        shelter_id: UUID of the shelter.
        count:      Number of evacuees checking out.

    Returns:
        The updated Shelter ORM instance.

    Raises:
        HTTPException 400: count exceeds current occupancy or invalid.
        HTTPException 404: Shelter not found.
        HTTPException 500: Database write failure.
    """
    shelter = _get_or_404(db, shelter_id)

    if count <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="count must be a positive integer (>= 1).",
        )

    if count > shelter.current_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot check out {count} evacuee(s). "
                f"Current occupancy is only {shelter.current_occupancy}."
            ),
        )

    shelter.current_occupancy -= count
    try:
        db.commit()
        db.refresh(shelter)
    except Exception as exc:
        db.rollback()
        logger.exception("Check-out failed for shelter %s: %s", shelter_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process check-out. Please try again.",
        ) from exc

    logger.info(
        "Shelter check-out: id=%s count=%s occupancy=%s/%s",
        shelter.id, count, shelter.current_occupancy, shelter.capacity,
    )
    return shelter
