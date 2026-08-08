"""
app/models/procurement.py

Emergency resource procurement network model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import ProcurementStatus


class ProcurementRequest(BaseModel):
    """
    Emergency Procurement Request record.
    """

    __tablename__ = "procurement_requests"

    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ProcurementStatus.REQUESTED.value)
