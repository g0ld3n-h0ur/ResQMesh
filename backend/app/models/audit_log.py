"""
app/models/audit_log.py

Append-oriented digital audit log model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.types import AutoJSON


class AuditLog(BaseModel):
    """
    Append-only digital audit trail record.
    """

    __tablename__ = "audit_logs"

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    previous_state: Mapped[Optional[dict]] = mapped_column(AutoJSON, nullable=True)
    new_state: Mapped[Optional[dict]] = mapped_column(AutoJSON, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
