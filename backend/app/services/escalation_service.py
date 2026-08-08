"""
app/services/escalation_service.py

Rule-based Automatic Escalation Engine.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.disaster import Disaster
from app.models.enums import DisasterSeverity, DisasterStatus
from app.models.audit_log import AuditLog


def run_escalation_checks(db: Session, unassigned_threshold_hours: float = 2.0) -> List[Dict[str, Any]]:
    """
    Check for critical incidents or SOS requests lacking resource assignment within threshold.
    """
    escalations: List[Dict[str, Any]] = []

    critical_disasters = (
        db.query(Disaster)
        .filter(
            Disaster.severity == DisasterSeverity.CRITICAL,
            Disaster.status.in_([DisasterStatus.REPORTED, DisasterStatus.VERIFIED]),
            Disaster.is_deleted == False,
        )
        .all()
    )

    now = datetime.datetime.now(datetime.timezone.utc)

    for disaster in critical_disasters:
        # Check elapsed time
        created = disaster.created_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=datetime.timezone.utc)

        elapsed_hours = (now - created).total_seconds() / 3600.0 if created else 3.0

        if elapsed_hours >= unassigned_threshold_hours:
            esc_data = {
                "disaster_id": str(disaster.id),
                "title": disaster.title,
                "severity": disaster.severity,
                "elapsed_hours": round(elapsed_hours, 1),
                "escalated_to": "District Officer / State Disaster Authority",
                "reason": f"Critical incident unassigned for > {unassigned_threshold_hours}h",
            }
            escalations.append(esc_data)

            # Record escalation in audit trail
            db.add(
                AuditLog(
                    action="INCIDENT_ESCALATED",
                    entity_type="Disaster",
                    entity_id=str(disaster.id),
                    previous_state={"status": disaster.status},
                    new_state={"escalated_to": esc_data["escalated_to"], "reason": esc_data["reason"]},
                )
            )

    db.commit()
    return escalations
