"""
app/models/road_closure.py

Road closures and blockages model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import ClosureReason


class RoadClosure(BaseModel):
    """
    Active road closure / blockage model for dynamic emergency vehicle rerouting.
    """

    __tablename__ = "road_closures"

    road_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_meters: Mapped[float] = mapped_column(Float, nullable=False, default=500.0)
    reason: Mapped[str] = mapped_column(String(100), nullable=False, default=ClosureReason.FLOOD.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reported_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
