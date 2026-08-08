"""
app/services/hospital_service.py

Business logic for the Hospital Management module.

Responsibilities
----------------
- Full CRUD (create, read, update, soft-delete)
- PATCH availability — targeted update of any capacity field subset
- List with filtering, keyword search, sorting, and pagination
- "Own record" guard — Hospital-role users may only update their own record
  (matched by current_user.organization_name == hospital.hospital_name,
   case-insensitive)
- Transaction rollback on all write failures

Filtering
---------
- search        : keyword across hospital_name and contact_number
- has_beds      : only hospitals with available_beds > 0
- has_icu       : only hospitals with icu_beds > 0
- has_ventilators : only hospitals with ventilators > 0
- has_ambulances  : only hospitals with ambulances > 0
- min_beds      : available_beds >= N
- min_icu       : icu_beds >= N

Sorting
-------
- newest   (created_at DESC, default)
- oldest   (created_at ASC)
- name     (hospital_name ASC)
- beds     (available_beds DESC)
- icu      (icu_beds DESC)

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

from app.models.hospital import Hospital
from app.models.user import User
from app.schemas.hospital import AvailabilityUpdate, HospitalCreate, HospitalUpdate

logger = logging.getLogger("app.services.hospital_service")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, hospital_id: UUID) -> Hospital:
    """Load a non-deleted Hospital by UUID, or raise HTTP 404."""
    stmt = (
        select(Hospital)
        .where(Hospital.id == hospital_id)
        .where(Hospital.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with id '{hospital_id}' not found.",
        )
    return obj


def _assert_own_record(hospital: Hospital, current_user: User) -> None:
    """
    Assert that a Hospital-role user is acting on their own facility record.

    Ownership is determined by case-insensitive equality between:
    - current_user.organization_name  (set at registration)
    - hospital.hospital_name

    Raises HTTP 403 if the names do not match.
    """
    user_org = (current_user.organization_name or "").strip().lower()
    hosp_name = hospital.hospital_name.strip().lower()
    if user_org != hosp_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access denied. Hospital users may only modify their own "
                "facility record. Your organisation name does not match "
                f"'{hospital.hospital_name}'."
            ),
        )


def _apply_filters(
    stmt,
    search: Optional[str],
    has_beds: Optional[bool],
    has_icu: Optional[bool],
    has_ventilators: Optional[bool],
    has_ambulances: Optional[bool],
    min_beds: Optional[int],
    min_icu: Optional[int],
):
    """Apply all optional query filters to a Hospital select statement."""
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Hospital.hospital_name.ilike(term),
                Hospital.contact_number.ilike(term),
            )
        )
    if has_beds is True:
        stmt = stmt.where(Hospital.available_beds > 0)
    if has_icu is True:
        stmt = stmt.where(Hospital.icu_beds > 0)
    if has_ventilators is True:
        stmt = stmt.where(Hospital.ventilators > 0)
    if has_ambulances is True:
        stmt = stmt.where(Hospital.ambulances > 0)
    if min_beds is not None and min_beds > 0:
        stmt = stmt.where(Hospital.available_beds >= min_beds)
    if min_icu is not None and min_icu > 0:
        stmt = stmt.where(Hospital.icu_beds >= min_icu)
    return stmt


def _resolve_sort(sort_by: str):
    """Return ORDER BY expression(s) for the requested sort key."""
    _map = {
        "newest": (Hospital.created_at.desc(),),
        "oldest": (Hospital.created_at.asc(),),
        "name": (Hospital.hospital_name.asc(),),
        "beds": (Hospital.available_beds.desc(), Hospital.created_at.desc()),
        "icu": (Hospital.icu_beds.desc(), Hospital.created_at.desc()),
    }
    return _map.get(sort_by, (Hospital.created_at.desc(),))


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_hospital(db: Session, data: HospitalCreate) -> Hospital:
    """
    Register a new hospital in the ResQMesh network.

    Args:
        db:   Active database session.
        data: Validated HospitalCreate payload.

    Returns:
        The newly created Hospital ORM instance.

    Raises:
        HTTPException 409: A non-deleted hospital with the same name exists.
        HTTPException 500: Database write failure.
    """
    # Duplicate name guard
    exists_stmt = (
        select(func.count())
        .select_from(Hospital)
        .where(Hospital.hospital_name.ilike(data.hospital_name))
        .where(Hospital.is_deleted.is_(False))
    )
    if db.execute(exists_stmt).scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A hospital named '{data.hospital_name}' is already registered. "
                "Use a unique hospital name."
            ),
        )

    hospital = Hospital(
        hospital_name=data.hospital_name,
        latitude=data.latitude,
        longitude=data.longitude,
        available_beds=data.available_beds,
        icu_beds=data.icu_beds,
        ventilators=data.ventilators,
        ambulances=data.ambulances,
        blood_units=data.blood_units,
        oxygen_units=data.oxygen_units,
        contact_number=data.contact_number,
    )
    try:
        db.add(hospital)
        db.commit()
        db.refresh(hospital)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create hospital: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register hospital. Please try again.",
        ) from exc

    logger.info("Hospital created: id=%s name=%r", hospital.id, hospital.hospital_name)
    return hospital


def get_hospital_by_id(db: Session, hospital_id: UUID) -> Hospital:
    """
    Retrieve a single non-deleted Hospital by UUID.

    Args:
        db:          Active database session.
        hospital_id: UUID of the hospital to fetch.

    Returns:
        The matching Hospital ORM instance.

    Raises:
        HTTPException 404: Hospital not found or soft-deleted.
    """
    return _get_or_404(db, hospital_id)


def list_hospitals(
    db: Session,
    search: Optional[str] = None,
    has_beds: Optional[bool] = None,
    has_icu: Optional[bool] = None,
    has_ventilators: Optional[bool] = None,
    has_ambulances: Optional[bool] = None,
    min_beds: Optional[int] = None,
    min_icu: Optional[int] = None,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Hospital], int]:
    """
    Return a filtered, searched, sorted, and paginated list of hospitals.

    Args:
        db:             Active database session.
        search:         Keyword search across hospital_name and contact_number.
        has_beds:       When True, only include hospitals with available_beds > 0.
        has_icu:        When True, only include hospitals with icu_beds > 0.
        has_ventilators: When True, only include hospitals with ventilators > 0.
        has_ambulances: When True, only include hospitals with ambulances > 0.
        min_beds:       Minimum required available_beds count.
        min_icu:        Minimum required icu_beds count.
        sort_by:        newest | oldest | name | beds | icu.
        page:           1-indexed page number.
        page_size:      Results per page.

    Returns:
        (list of Hospital ORM objects, total matching count)
    """
    base = select(Hospital).where(Hospital.is_deleted.is_(False))
    base = _apply_filters(
        base,
        search=search,
        has_beds=has_beds,
        has_icu=has_icu,
        has_ventilators=has_ventilators,
        has_ambulances=has_ambulances,
        min_beds=min_beds,
        min_icu=min_icu,
    )

    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    order_exprs = _resolve_sort(sort_by)
    items_stmt = (
        base.order_by(*order_exprs)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    hospitals = list(db.execute(items_stmt).scalars().all())
    return hospitals, total


def update_hospital(
    db: Session,
    hospital_id: UUID,
    data: HospitalUpdate,
    current_user: User,
) -> Hospital:
    """
    Partially update a Hospital record.

    Only fields explicitly included in the request body are modified.
    Hospital-role users may only update their own facility record.

    Args:
        db:          Active database session.
        hospital_id: UUID of the hospital to update.
        data:        Validated HospitalUpdate payload.
        current_user: Authenticated user performing the action.

    Returns:
        The updated Hospital ORM instance.

    Raises:
        HTTPException 403: Hospital user operating on another facility.
        HTTPException 404: Hospital not found.
        HTTPException 500: Database write failure.
    """
    from app.models.enums import RoleEnum

    hospital = _get_or_404(db, hospital_id)

    if current_user.role == RoleEnum.HOSPITAL:
        _assert_own_record(hospital, current_user)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hospital, field, value)

    try:
        db.commit()
        db.refresh(hospital)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update hospital %s: %s", hospital_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update hospital record. Please try again.",
        ) from exc

    logger.info("Hospital updated: id=%s", hospital.id)
    return hospital


def delete_hospital(db: Session, hospital_id: UUID) -> None:
    """
    Soft-delete a Hospital by setting is_deleted = True.

    Args:
        db:          Active database session.
        hospital_id: UUID of the hospital to soft-delete.

    Raises:
        HTTPException 404: Hospital not found.
        HTTPException 500: Database write failure.
    """
    hospital = _get_or_404(db, hospital_id)
    hospital.is_deleted = True
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete hospital %s: %s", hospital_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete hospital record. Please try again.",
        ) from exc

    logger.info("Hospital soft-deleted: id=%s", hospital_id)


# ---------------------------------------------------------------------------
# Availability update
# ---------------------------------------------------------------------------


def update_availability(
    db: Session,
    hospital_id: UUID,
    data: AvailabilityUpdate,
    current_user: User,
) -> Hospital:
    """
    Update one or more capacity/availability fields of a Hospital record.

    This is a targeted PATCH for real-time capacity updates — only the
    fields explicitly provided in the payload are modified.  All numeric
    fields are validated to be >= 0 by the schema.

    Hospital-role users may only update their own facility record.

    Args:
        db:          Active database session.
        hospital_id: UUID of the hospital to update.
        data:        Validated AvailabilityUpdate payload.
        current_user: Authenticated user performing the action.

    Returns:
        The updated Hospital ORM instance.

    Raises:
        HTTPException 403: Hospital user operating on another facility.
        HTTPException 404: Hospital not found.
        HTTPException 500: Database write failure.
    """
    from app.models.enums import RoleEnum

    hospital = _get_or_404(db, hospital_id)

    if current_user.role == RoleEnum.HOSPITAL:
        _assert_own_record(hospital, current_user)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one availability field must be provided.",
        )

    for field, value in update_data.items():
        setattr(hospital, field, value)

    try:
        db.commit()
        db.refresh(hospital)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to update availability for hospital %s: %s", hospital_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update hospital availability. Please try again.",
        ) from exc

    logger.info(
        "Hospital availability updated: id=%s fields=%s",
        hospital.id,
        list(update_data.keys()),
    )
    return hospital
