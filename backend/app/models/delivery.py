"""
app/models/delivery.py

Post-disaster proof of delivery model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import DeliveryStatus


class ProofOfDelivery(BaseModel):
    """
    Proof of Delivery record with discrepancy calculation.
    """

    __tablename__ = "proof_of_deliveries"

    assignment_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    dispatched_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discrepancy_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=DeliveryStatus.SENT.value)
