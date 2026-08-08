"""
app/models/anomaly.py

Rule-based anomaly detection record model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import AnomalySeverity


class AnomalyRecord(BaseModel):
    """
    Deterministic anomaly detection audit record.
    """

    __tablename__ = "anomaly_records"

    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default=AnomalySeverity.MEDIUM.value)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNRESOLVED")
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
