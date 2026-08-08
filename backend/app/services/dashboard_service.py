"""
app/services/dashboard_service.py

Business logic for the Dashboard module.

Aggregates data from existing ORM models to produce summary metrics,
counts, and status breakdowns for the ResQMesh frontend dashboard.

No ML, no prediction — pure SQL aggregations only.

Functions
---------
get_summary()       → Platform-wide KPI counts in one query bundle
get_statistics()    → Breakdown counts per enum value (status, severity…)
get_disasters()     → Top-N active disaster events with key fields
get_resources()     → Resource inventory summary grouped by status + type
get_hospitals()     → Hospital capacity summary (total/available beds, ICU…)

All read queries use SQLAlchemy 2.0 select() / func() API.
All data is returned as plain Python dicts — no ORM objects leave this
module, so the router needs no serialisation beyond JSON dumping.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.disaster import Disaster
from app.models.emergency_report import EmergencyReport
from app.models.enums import (
    AssignmentStatus,
    DisasterSeverity,
    DisasterStatus,
    ResourceStatus,
    RoleEnum,
)
from app.models.hospital import Hospital
from app.models.notification import Notification
from app.models.resource import Resource
from app.models.shelter import Shelter
from app.models.user import User

logger = logging.getLogger("app.services.dashboard_service")


# ---------------------------------------------------------------------------
# Internal helper — runs a scalar count with a where clause
# ---------------------------------------------------------------------------


def _count(db: Session, model, *where_clauses) -> int:
    """Execute a COUNT(*) query on model with optional WHERE clauses."""
    stmt = select(func.count()).select_from(model)
    for clause in where_clauses:
        stmt = stmt.where(clause)
    return db.execute(stmt).scalar_one()


# ---------------------------------------------------------------------------
# Summary endpoint
# ---------------------------------------------------------------------------


def get_summary(db: Session) -> dict[str, Any]:
    """
    Return a single-shot platform-wide KPI summary.

    Counts across all major entities — one round-trip per entity type.

    Returns:
        dict with top-level integer counters for the summary dashboard card.
    """
    # Disaster counts
    total_disasters = _count(db, Disaster, Disaster.is_deleted.is_(False))
    active_disasters = _count(
        db, Disaster,
        Disaster.is_deleted.is_(False),
        Disaster.status.in_([
            DisasterStatus.REPORTED,
            DisasterStatus.VERIFIED,
            DisasterStatus.RESOURCE_ALLOCATED,
            DisasterStatus.RESCUE_ONGOING,
        ]),
    )
    resolved_disasters = _count(
        db, Disaster,
        Disaster.is_deleted.is_(False),
        Disaster.status == DisasterStatus.RESOLVED,
    )

    # Emergency reports
    total_reports = _count(db, EmergencyReport, EmergencyReport.is_deleted.is_(False))
    unverified_reports = _count(
        db, EmergencyReport,
        EmergencyReport.is_deleted.is_(False),
        EmergencyReport.linked_disaster_id.is_(None),
    )

    # Resources
    total_resources = _count(db, Resource, Resource.is_deleted.is_(False))
    available_resources = _count(
        db, Resource,
        Resource.is_deleted.is_(False),
        Resource.status == ResourceStatus.AVAILABLE,
    )
    allocated_resources = _count(
        db, Resource,
        Resource.is_deleted.is_(False),
        Resource.status == ResourceStatus.ALLOCATED,
    )

    # Shelters
    shelter_stats = db.execute(
        select(
            func.count(Shelter.id).label("total"),
            func.coalesce(func.sum(Shelter.capacity), 0).label("total_capacity"),
            func.coalesce(func.sum(Shelter.current_occupancy), 0).label("total_occupancy"),
        ).where(Shelter.is_deleted.is_(False))
    ).one()

    # Hospitals
    hospital_stats = db.execute(
        select(
            func.count(Hospital.id).label("total"),
            func.coalesce(func.sum(Hospital.available_beds), 0).label("total_beds"),
            func.coalesce(func.sum(Hospital.icu_beds), 0).label("total_icu"),
        ).where(Hospital.is_deleted.is_(False))
    ).one()

    # Assignments
    total_assignments = _count(db, Assignment, Assignment.is_deleted.is_(False))
    active_assignments = _count(
        db, Assignment,
        Assignment.is_deleted.is_(False),
        Assignment.status == AssignmentStatus.IN_PROGRESS,
    )

    # Users
    total_users = _count(db, User, User.is_deleted.is_(False), User.is_active.is_(True))
    total_volunteers = _count(
        db, User,
        User.is_deleted.is_(False),
        User.is_active.is_(True),
        User.role == RoleEnum.VOLUNTEER,
    )

    # Unread notifications
    unread_notifications = _count(
        db, Notification,
        Notification.is_deleted.is_(False),
        Notification.is_read.is_(False),
    )

    return {
        "disasters": {
            "total": total_disasters,
            "active": active_disasters,
            "resolved": resolved_disasters,
        },
        "emergency_reports": {
            "total": total_reports,
            "unverified": unverified_reports,
            "verified": total_reports - unverified_reports,
        },
        "resources": {
            "total": total_resources,
            "available": available_resources,
            "allocated": allocated_resources,
        },
        "shelters": {
            "total": int(shelter_stats.total),
            "total_capacity": int(shelter_stats.total_capacity),
            "current_occupancy": int(shelter_stats.total_occupancy),
            "available_spots": max(
                0,
                int(shelter_stats.total_capacity) - int(shelter_stats.total_occupancy),
            ),
        },
        "hospitals": {
            "total": int(hospital_stats.total),
            "total_available_beds": int(hospital_stats.total_beds),
            "total_icu_beds": int(hospital_stats.total_icu),
        },
        "assignments": {
            "total": total_assignments,
            "active": active_assignments,
        },
        "users": {
            "total_active": total_users,
            "volunteers": total_volunteers,
        },
        "notifications": {
            "unread": unread_notifications,
        },
    }


# ---------------------------------------------------------------------------
# Statistics endpoint
# ---------------------------------------------------------------------------


def get_statistics(db: Session) -> dict[str, Any]:
    """
    Return breakdown counts per enum value across core entities.

    Provides per-value counts for status/severity fields — used for
    chart/graph rendering on the frontend.

    Returns:
        dict with enumerated breakdowns for disasters, resources,
        assignments, and users.
    """
    # Disaster by status
    disaster_by_status = {s.value: 0 for s in DisasterStatus}
    rows = db.execute(
        select(Disaster.status, func.count(Disaster.id))
        .where(Disaster.is_deleted.is_(False))
        .group_by(Disaster.status)
    ).all()
    for row_status, row_count in rows:
        disaster_by_status[row_status] = row_count

    # Disaster by severity
    disaster_by_severity = {s.value: 0 for s in DisasterSeverity}
    rows = db.execute(
        select(Disaster.severity, func.count(Disaster.id))
        .where(Disaster.is_deleted.is_(False))
        .group_by(Disaster.severity)
    ).all()
    for row_severity, row_count in rows:
        disaster_by_severity[row_severity] = row_count

    # Resources by status
    resources_by_status = {s.value: 0 for s in ResourceStatus}
    rows = db.execute(
        select(Resource.status, func.count(Resource.id))
        .where(Resource.is_deleted.is_(False))
        .group_by(Resource.status)
    ).all()
    for row_status, row_count in rows:
        resources_by_status[row_status] = row_count

    # Resources by type (top-10 by count)
    resources_by_type: dict[str, int] = {}
    rows = db.execute(
        select(Resource.resource_type, func.count(Resource.id))
        .where(Resource.is_deleted.is_(False))
        .group_by(Resource.resource_type)
        .order_by(func.count(Resource.id).desc())
        .limit(10)
    ).all()
    for row_type, row_count in rows:
        resources_by_type[row_type] = row_count

    # Assignments by status
    assignments_by_status = {s.value: 0 for s in AssignmentStatus}
    rows = db.execute(
        select(Assignment.status, func.count(Assignment.id))
        .where(Assignment.is_deleted.is_(False))
        .group_by(Assignment.status)
    ).all()
    for row_status, row_count in rows:
        assignments_by_status[row_status] = row_count

    # Users by role (active only)
    users_by_role = {r.value: 0 for r in RoleEnum}
    rows = db.execute(
        select(User.role, func.count(User.id))
        .where(User.is_deleted.is_(False))
        .where(User.is_active.is_(True))
        .group_by(User.role)
    ).all()
    for row_role, row_count in rows:
        users_by_role[row_role] = row_count

    return {
        "disasters": {
            "by_status": disaster_by_status,
            "by_severity": disaster_by_severity,
        },
        "resources": {
            "by_status": resources_by_status,
            "by_type": resources_by_type,
        },
        "assignments": {
            "by_status": assignments_by_status,
        },
        "users": {
            "by_role": users_by_role,
        },
    }


# ---------------------------------------------------------------------------
# Disaster snapshot endpoint
# ---------------------------------------------------------------------------


def get_disasters_snapshot(db: Session, limit: int = 10) -> list[dict[str, Any]]:
    """
    Return the most recent active disaster events.

    Active = not resolved and not soft-deleted.

    Args:
        db:    Active database session.
        limit: Maximum number of records to return (default 10, max 50).

    Returns:
        List of dicts with key disaster fields.
    """
    limit = min(limit, 50)
    stmt = (
        select(Disaster)
        .where(Disaster.is_deleted.is_(False))
        .where(Disaster.status != DisasterStatus.RESOLVED)
        .order_by(Disaster.created_at.desc())
        .limit(limit)
    )
    disasters = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "disaster_type": d.disaster_type,
            "severity": d.severity,
            "status": d.status,
            "location": d.location,
            "created_at": d.created_at.isoformat(),
        }
        for d in disasters
    ]


# ---------------------------------------------------------------------------
# Resource inventory snapshot endpoint
# ---------------------------------------------------------------------------


def get_resources_snapshot(db: Session) -> dict[str, Any]:
    """
    Return an aggregated resource inventory summary.

    Provides total and available quantity sums broken down by resource type,
    plus overall totals.

    Returns:
        dict with total counts, quantity sums, and per-type breakdown.
    """
    # Overall totals
    totals = db.execute(
        select(
            func.count(Resource.id).label("total_records"),
            func.coalesce(func.sum(Resource.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(Resource.available_quantity), 0).label(
                "available_quantity"
            ),
        ).where(Resource.is_deleted.is_(False))
    ).one()

    # Per-type breakdown
    rows = db.execute(
        select(
            Resource.resource_type,
            func.count(Resource.id).label("record_count"),
            func.coalesce(func.sum(Resource.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(Resource.available_quantity), 0).label(
                "available_quantity"
            ),
        )
        .where(Resource.is_deleted.is_(False))
        .group_by(Resource.resource_type)
        .order_by(Resource.resource_type.asc())
    ).all()

    by_type = [
        {
            "resource_type": row.resource_type,
            "record_count": row.record_count,
            "total_quantity": int(row.total_quantity),
            "available_quantity": int(row.available_quantity),
        }
        for row in rows
    ]

    return {
        "total_records": int(totals.total_records),
        "total_quantity": int(totals.total_quantity),
        "available_quantity": int(totals.available_quantity),
        "by_type": by_type,
    }


# ---------------------------------------------------------------------------
# Hospital capacity snapshot endpoint
# ---------------------------------------------------------------------------


def get_hospitals_snapshot(db: Session, limit: int = 10) -> dict[str, Any]:
    """
    Return aggregated hospital capacity metrics plus a top-N list.

    Args:
        db:    Active database session.
        limit: Maximum number of individual hospital records (default 10, max 50).

    Returns:
        dict with fleet-wide totals and a list of hospitals sorted by
        available beds (descending).
    """
    limit = min(limit, 50)

    # Platform-wide capacity totals
    totals = db.execute(
        select(
            func.count(Hospital.id).label("total"),
            func.coalesce(func.sum(Hospital.available_beds), 0).label("total_beds"),
            func.coalesce(func.sum(Hospital.icu_beds), 0).label("total_icu"),
            func.coalesce(func.sum(Hospital.ventilators), 0).label("total_ventilators"),
            func.coalesce(func.sum(Hospital.ambulances), 0).label("total_ambulances"),
            func.coalesce(func.sum(Hospital.blood_units), 0).label("total_blood_units"),
            func.coalesce(func.sum(Hospital.oxygen_units), 0).label("total_oxygen_units"),
        ).where(Hospital.is_deleted.is_(False))
    ).one()

    # Top hospitals by available beds
    hospitals = db.execute(
        select(Hospital)
        .where(Hospital.is_deleted.is_(False))
        .order_by(Hospital.available_beds.desc(), Hospital.icu_beds.desc())
        .limit(limit)
    ).scalars().all()

    hospitals_list = [
        {
            "id": str(h.id),
            "hospital_name": h.hospital_name,
            "available_beds": h.available_beds,
            "icu_beds": h.icu_beds,
            "ventilators": h.ventilators,
            "ambulances": h.ambulances,
            "blood_units": h.blood_units,
            "oxygen_units": h.oxygen_units,
            "contact_number": h.contact_number,
            "latitude": h.latitude,
            "longitude": h.longitude,
        }
        for h in hospitals
    ]

    return {
        "totals": {
            "total_hospitals": int(totals.total),
            "total_available_beds": int(totals.total_beds),
            "total_icu_beds": int(totals.total_icu),
            "total_ventilators": int(totals.total_ventilators),
            "total_ambulances": int(totals.total_ambulances),
            "total_blood_units": int(totals.total_blood_units),
            "total_oxygen_units": int(totals.total_oxygen_units),
        },
        "hospitals": hospitals_list,
    }


def get_shelters_snapshot(db: Session, limit: int = 10) -> list[dict[str, Any]]:
    """
    Return recent active shelter records for dashboard overview.
    """
    limit = min(limit, 50)
    shelters = db.execute(
        select(Shelter)
        .where(Shelter.is_deleted.is_(False))
        .order_by(Shelter.created_at.desc())
        .limit(limit)
    ).scalars().all()

    return [
        {
            "id": str(s.id),
            "shelter_name": s.shelter_name,
            "capacity": s.capacity,
            "current_occupancy": s.current_occupancy,
            "district": getattr(s, "district", "Chennai"),
            "state": getattr(s, "state", "Tamil Nadu"),
            "latitude": s.latitude,
            "longitude": s.longitude,
        }
        for s in shelters
    ]
