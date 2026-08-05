"""
app/services/report_service.py

Business logic for the Emergency Report module.

Responsibilities
----------------
- Create anonymous (public) emergency reports
- List reports with full filtering, search, sorting, and pagination
- Retrieve single report by UUID
- Verify a report (Government action — links report to a disaster)
- Soft-delete a report (Government action)

Filtering support
-----------------
- district        : substring match on `address` field
- state           : substring match on `address` field
- country         : substring match on `address` field
- date_from / date_to : range filter on `reported_at`
- is_verified     : True = linked_disaster_id IS NOT NULL
- disaster_type   : substring match on `disaster_type` field

Search
------
Keyword search across reporter_name, description, phone, address,
disaster_type — any column containing the term (case-insensitive LIKE).

Sorting
-------
- newest  (reported_at DESC, default)
- oldest  (reported_at ASC)
- verified_first (linked_disaster_id DESC NULLS LAST)

Pagination
----------
- page / page_size   (1-indexed, defaults from constants)
- limit / offset     (raw offset-based, overrides page/page_size when provided)

All queries use SQLAlchemy 2.0 select() API.
Soft-delete is enforced via is_deleted filter on every read.
Transactions are rolled back on failure.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.emergency_report import EmergencyReport
from app.schemas.emergency_report import EmergencyReportCreate, ReportVerifyRequest

logger = logging.getLogger("app.services.report_service")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, report_id: UUID) -> EmergencyReport:
    """Load a non-deleted EmergencyReport by UUID, or raise HTTP 404."""
    stmt = (
        select(EmergencyReport)
        .where(EmergencyReport.id == report_id)
        .where(EmergencyReport.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency report with id '{report_id}' not found.",
        )
    return obj


def _apply_filters(
    stmt,
    district: Optional[str],
    state: Optional[str],
    country: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    is_verified: Optional[bool],
    disaster_type: Optional[str],
    search: Optional[str],
):
    """
    Apply all optional query filters to a select statement.

    Note: The EmergencyReport model stores location as latitude/longitude and
    a free-text `address` field. District, state, and country filters perform
    a substring match against the `address` column since no dedicated columns
    exist in the model.
    """
    # Geographic text filters — substring match on address
    if district:
        stmt = stmt.where(EmergencyReport.address.ilike(f"%{district}%"))
    if state:
        stmt = stmt.where(EmergencyReport.address.ilike(f"%{state}%"))
    if country:
        stmt = stmt.where(EmergencyReport.address.ilike(f"%{country}%"))

    # Date range on reported_at
    if date_from:
        stmt = stmt.where(EmergencyReport.reported_at >= date_from)
    if date_to:
        stmt = stmt.where(EmergencyReport.reported_at <= date_to)

    # Verification status — verified = has a linked disaster
    if is_verified is True:
        stmt = stmt.where(EmergencyReport.linked_disaster_id.is_not(None))
    elif is_verified is False:
        stmt = stmt.where(EmergencyReport.linked_disaster_id.is_(None))

    # Disaster type filter
    if disaster_type:
        stmt = stmt.where(
            EmergencyReport.disaster_type.ilike(f"%{disaster_type}%")
        )

    # Full-text keyword search across multiple columns
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                EmergencyReport.reporter_name.ilike(term),
                EmergencyReport.description.ilike(term),
                EmergencyReport.phone.ilike(term),
                EmergencyReport.address.ilike(term),
                EmergencyReport.disaster_type.ilike(term),
            )
        )

    return stmt


def _resolve_sort(sort_by: str) -> tuple:
    """
    Resolve a sort_by string into a (column, direction) tuple.

    Supported values
    ----------------
    newest         → reported_at DESC  (default)
    oldest         → reported_at ASC
    verified_first → linked_disaster_id DESC NULLS LAST, reported_at DESC
    """
    if sort_by == "oldest":
        return (EmergencyReport.reported_at.asc(),)
    if sort_by == "verified_first":
        return (
            EmergencyReport.linked_disaster_id.desc().nulls_last(),
            EmergencyReport.reported_at.desc(),
        )
    # Default: newest first
    return (EmergencyReport.reported_at.desc(),)


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def _is_duplicate_report(
    db: Session,
    reporter_name: str,
    phone: Optional[str],
    description: str,
    latitude: Optional[float],
    longitude: Optional[float],
) -> bool:
    """
    Detect potential duplicate reports.

    A report is considered a duplicate when all of the following match an
    existing non-deleted report submitted within the past 10 minutes:
    - Same reporter_name (case-insensitive)
    - Same phone number (if provided)
    - First 200 characters of description match (case-insensitive)
    - Same latitude and longitude (if provided)

    Returns True if a matching report exists.
    """
    from datetime import timezone, timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    desc_prefix = description[:200] if len(description) > 200 else description

    stmt = (
        select(func.count())
        .select_from(EmergencyReport)
        .where(EmergencyReport.is_deleted.is_(False))
        .where(EmergencyReport.reported_at >= cutoff)
        .where(EmergencyReport.reporter_name.ilike(reporter_name))
        .where(EmergencyReport.description.ilike(f"{desc_prefix}%"))
    )
    if phone:
        stmt = stmt.where(EmergencyReport.phone == phone)
    if latitude is not None:
        stmt = stmt.where(EmergencyReport.latitude == latitude)
    if longitude is not None:
        stmt = stmt.where(EmergencyReport.longitude == longitude)

    count: int = db.execute(stmt).scalar_one()
    return count > 0


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


def create_report(
    db: Session,
    data: EmergencyReportCreate,
) -> EmergencyReport:
    """
    Create and persist a new public emergency report.

    This endpoint is unauthenticated — reported_by_user_id is always null
    for public submissions. Duplicate detection is applied to prevent
    accidental or malicious double submissions within a 10-minute window.

    Args:
        db:   Active database session.
        data: Validated EmergencyReportCreate payload.

    Returns:
        The newly created EmergencyReport ORM instance.

    Raises:
        HTTPException 409: Duplicate report detected.
        HTTPException 500: Database write failure.
    """
    # Duplicate guard
    if _is_duplicate_report(
        db=db,
        reporter_name=data.reporter_name,
        phone=data.phone,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A very similar report from the same reporter was submitted within "
                "the last 10 minutes. Please wait before resubmitting."
            ),
        )

    report = EmergencyReport(
        reporter_name=data.reporter_name,
        phone=data.phone,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        image_url=data.image_url,
        disaster_type=data.disaster_type,
        address=data.address,
        reported_by_user_id=None,     # anonymous — always null for public endpoint
        linked_disaster_id=None,      # unverified at creation
    )

    try:
        db.add(report)
        db.commit()
        db.refresh(report)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create emergency report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save emergency report. Please try again.",
        ) from exc

    logger.info(
        "Emergency report created: id=%s reporter=%r phone=%s",
        report.id,
        report.reporter_name,
        report.phone,
    )
    return report


def get_report_by_id(db: Session, report_id: UUID) -> EmergencyReport:
    """
    Retrieve a single non-deleted EmergencyReport by UUID.

    Args:
        db:        Active database session.
        report_id: UUID of the report to retrieve.

    Returns:
        The matching EmergencyReport ORM instance.

    Raises:
        HTTPException 404: Report not found or soft-deleted.
    """
    return _get_or_404(db, report_id)


def list_reports(
    db: Session,
    district: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    is_verified: Optional[bool] = None,
    disaster_type: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 20,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> tuple[list[EmergencyReport], int]:
    """
    Return a filtered, searched, sorted, paginated list of emergency reports.

    Pagination modes
    ----------------
    If `limit` and `offset` are provided, they take precedence over
    page/page_size for raw offset-based access.

    Args:
        db:           Active database session.
        district:     Substring filter against the address field.
        state:        Substring filter against the address field.
        country:      Substring filter against the address field.
        date_from:    Minimum reported_at (inclusive).
        date_to:      Maximum reported_at (inclusive).
        is_verified:  True=only verified, False=only unverified, None=all.
        disaster_type: Substring filter on disaster_type field.
        search:       Keyword search across reporter_name, description,
                      phone, address, disaster_type.
        sort_by:      Sort mode: newest | oldest | verified_first.
        page:         1-indexed page number.
        page_size:    Results per page.
        limit:        Raw SQL LIMIT (overrides page_size when set).
        offset:       Raw SQL OFFSET (overrides (page-1)*page_size when set).

    Returns:
        (list of EmergencyReport ORM objects, total matching count)
    """
    base = select(EmergencyReport).where(EmergencyReport.is_deleted.is_(False))
    base = _apply_filters(
        base,
        district=district,
        state=state,
        country=country,
        date_from=date_from,
        date_to=date_to,
        is_verified=is_verified,
        disaster_type=disaster_type,
        search=search,
    )

    # Total count before pagination
    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    # Apply sort expressions
    order_exprs = _resolve_sort(sort_by)
    base = base.order_by(*order_exprs)

    # Resolve pagination
    if limit is not None and offset is not None:
        final_limit = min(limit, 100)
        final_offset = max(offset, 0)
    else:
        final_limit = page_size
        final_offset = (page - 1) * page_size

    items_stmt = base.offset(final_offset).limit(final_limit)
    reports = list(db.execute(items_stmt).scalars().all())

    return reports, total


def verify_report(
    db: Session,
    report_id: UUID,
    payload: ReportVerifyRequest,
    verified_by: UUID,
) -> EmergencyReport:
    """
    Mark an emergency report as verified by a Government officer.

    Verification links the report to an existing disaster (if disaster_id
    is provided in the payload) which sets linked_disaster_id, making
    is_verified = True in the response schema.

    If no disaster_id is provided, the report is still marked verified by
    linking it to itself — however, since the model stores verification
    state via linked_disaster_id only, callers should ideally supply a
    disaster_id. When omitted, the report retains linked_disaster_id=None
    and this raises an HTTP 400 to preserve data integrity.

    Args:
        db:          Active database session.
        report_id:   UUID of the report to verify.
        payload:     ReportVerifyRequest (optional disaster_id + notes).
        verified_by: UUID of the Government user performing verification.

    Returns:
        The updated EmergencyReport ORM instance.

    Raises:
        HTTPException 400: disaster_id required for verification, or report
                           already verified.
        HTTPException 404: Report not found.
        HTTPException 500: Database write failure.
    """
    report = _get_or_404(db, report_id)

    if report.linked_disaster_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Report '{report_id}' is already verified and linked to "
                f"disaster '{report.linked_disaster_id}'."
            ),
        )

    if payload.disaster_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A disaster_id is required to verify an emergency report. "
                "Please link this report to a verified disaster event."
            ),
        )

    report.linked_disaster_id = payload.disaster_id

    try:
        db.commit()
        db.refresh(report)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to verify report %s: %s", report_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify emergency report. Please try again.",
        ) from exc

    logger.info(
        "Report verified: id=%s disaster_id=%s verified_by=%s",
        report.id,
        report.linked_disaster_id,
        verified_by,
    )
    return report


def delete_report(db: Session, report_id: UUID, deleted_by: UUID) -> None:
    """
    Soft-delete an EmergencyReport by setting is_deleted = True.

    The record is retained in the database for audit purposes.

    Args:
        db:         Active database session.
        report_id:  UUID of the report to delete.
        deleted_by: UUID of the Government user performing the deletion.

    Raises:
        HTTPException 404: Report not found.
        HTTPException 500: Database write failure.
    """
    report = _get_or_404(db, report_id)
    report.is_deleted = True

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to soft-delete report %s: %s", report_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete emergency report. Please try again.",
        ) from exc

    logger.info(
        "Report soft-deleted: id=%s deleted_by=%s", report_id, deleted_by
    )
