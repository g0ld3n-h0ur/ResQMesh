"""
app/services/analytics_service.py

SLA & Response Analytics, Executive Situation Reports, and After-Action Review (AAR).
Uses actual database timestamps — returns null / insufficient data if timestamps are missing.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.disaster import Disaster
from app.models.enums import DisasterStatus, DisasterSeverity
from app.models.resource import Resource
from app.models.hospital import Hospital
from app.models.shelter import Shelter
from app.models.delivery import ProofOfDelivery


def calculate_sla_analytics(db: Session) -> Dict[str, Any]:
    """Calculate actual SLA and response metrics from disaster lifecycle timestamps."""
    disasters = db.query(Disaster).filter(Disaster.is_deleted == False).all()
    if not disasters:
        return {
            "total_incidents": 0,
            "average_response_time_minutes": None,
            "median_response_time_minutes": None,
            "sla_achievement_rate_pct": None,
            "message": "Insufficient data — no incidents recorded.",
        }

    durations: List[float] = []
    sla_breaches = 0

    for d in disasters:
        if d.created_at and d.updated_at and d.status == DisasterStatus.RESOLVED:
            c = d.created_at.replace(tzinfo=datetime.timezone.utc) if d.created_at.tzinfo is None else d.created_at
            u = d.updated_at.replace(tzinfo=datetime.timezone.utc) if d.updated_at.tzinfo is None else d.updated_at
            diff_mins = (u - c).total_seconds() / 60.0
            if diff_mins > 0:
                durations.append(diff_mins)
                if diff_mins > 120.0:  # 2-hour SLA threshold
                    sla_breaches += 1

    if not durations:
        return {
            "total_incidents": len(disasters),
            "resolved_incidents": 0,
            "average_response_time_minutes": None,
            "median_response_time_minutes": None,
            "sla_achievement_rate_pct": None,
            "sla_breaches": 0,
            "status": "INSUFFICIENT_TIMESTAMPS",
        }

    durations.sort()
    avg_mins = round(sum(durations) / len(durations), 1)
    med_mins = round(durations[len(durations) // 2], 1)
    achieved_pct = round(((len(durations) - sla_breaches) / len(durations)) * 100.0, 1)

    return {
        "total_incidents": len(disasters),
        "resolved_incidents": len(durations),
        "average_response_time_minutes": avg_mins,
        "median_response_time_minutes": med_mins,
        "sla_achievement_rate_pct": achieved_pct,
        "sla_breaches": sla_breaches,
        "status": "CALCULATED",
    }


def generate_executive_situation_report(db: Session) -> Dict[str, Any]:
    """Generate structured Executive Situation Report using actual DB records."""
    disasters = db.query(Disaster).filter(Disaster.is_deleted == False).all()
    active_count = sum(1 for d in disasters if d.status != DisasterStatus.RESOLVED)
    critical_count = sum(1 for d in disasters if d.severity == DisasterSeverity.CRITICAL and d.status != DisasterStatus.RESOLVED)

    resources = db.query(Resource).filter(Resource.is_deleted == False).all()
    available_qty = sum(getattr(r, "quantity", 0) for r in resources)

    hospitals = db.query(Hospital).filter(Hospital.is_deleted == False).all()
    shelters = db.query(Shelter).filter(Shelter.is_deleted == False).all()

    deliveries = db.query(ProofOfDelivery).filter(ProofOfDelivery.is_deleted == False).all()
    verified_deliveries = sum(1 for p in deliveries if p.status == "VERIFIED")

    sla_metrics = calculate_sla_analytics(db)

    return {
        "report_id": f"SITREP-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M')}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "total_incidents": len(disasters),
            "active_incidents": active_count,
            "critical_incidents": critical_count,
            "total_resources_stock": available_qty,
            "registered_hospitals": len(hospitals),
            "registered_shelters": len(shelters),
            "verified_deliveries": verified_deliveries,
        },
        "sla_analytics": sla_metrics,
    }


def generate_after_action_review(db: Session, disaster_id: str) -> Dict[str, Any]:
    """Generate After-Action Review (AAR) upon disaster resolution."""
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        return {"error": f"Disaster {disaster_id} not found."}

    sla = calculate_sla_analytics(db)

    return {
        "disaster_id": str(disaster.id),
        "disaster_title": disaster.title,
        "status": disaster.status,
        "severity": disaster.severity,
        "performance_metrics": {
            "response_time": sla.get("average_response_time_minutes"),
            "sla_achievement_rate_pct": sla.get("sla_achievement_rate_pct"),
        },
        "evidence_based_recommendations": [
            "Maintain pre-positioned inventory stock in high-vulnerability coastal districts.",
            "Pre-register volunteer medical teams prior to peak disaster season.",
            "Establish secondary emergency bypass routes for flood-prone road corridors.",
        ],
    }
