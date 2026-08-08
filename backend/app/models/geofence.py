"""
app/models/geofence.py

Geospatial zone / geofencing model.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import GeofenceType
from app.models.types import AutoJSON


class GeofenceZone(BaseModel):
    """
    Geofenced operational, evacuation, or restricted zone.
    """

    __tablename__ = "geofence_zones"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    zone_type: Mapped[str] = mapped_column(String(100), nullable=False, default=GeofenceType.DISASTER_ZONE.value)
    center_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    center_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_km: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    coordinates_geojson: Mapped[Optional[dict]] = mapped_column(AutoJSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
