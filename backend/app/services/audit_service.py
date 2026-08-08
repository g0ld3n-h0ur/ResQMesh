"""
app/services/audit_service.py

Digital Audit Trail Service.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    actor_id: Optional[uuid.UUID] = None,
    actor_role: str = "system",
    organization_id: Optional[uuid.UUID] = None,
    entity_id: Optional[str] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> AuditLog:
    """Log an append-only digital audit trail entry."""
    if idempotency_key:
        existing = db.query(AuditLog).filter(AuditLog.idempotency_key == idempotency_key).first()
        if existing:
            return existing

    log_entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        organization_id=organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        previous_state=previous_state,
        new_state=new_state,
        idempotency_key=idempotency_key,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(db: Session, limit: int = 50) -> List[AuditLog]:
    """Retrieve audit logs."""
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
