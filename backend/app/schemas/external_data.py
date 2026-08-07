"""
app/schemas/external_data.py

Pydantic v2 schemas for the unified external situational feed — see
app/services/external_data_service.py for where the data actually comes from.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class WeatherSnapshot(BaseSchema):
    """Live current-conditions snapshot from Open-Meteo for one coordinate."""

    temperature_c: float | None = None
    humidity_pct: float | None = None
    precipitation_mm: float | None = None
    rain_mm: float | None = None
    wind_speed_kmh: float | None = None
    observed_at: str | None = None
    source: str = "Open-Meteo"


class EarthquakeEvent(BaseSchema):
    """A single significant earthquake event from the USGS feed."""

    id: str | None = None
    place: str | None = None
    magnitude: float | None = None
    time: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    url: str | None = None
    source: str = "USGS"


class DisasterWeatherContext(BaseSchema):
    """Live weather context for one active disaster."""

    disaster_id: UUID
    title: str
    district: str | None = None
    state: str | None = None
    weather: WeatherSnapshot | None = None
    weather_available: bool = Field(
        ..., description="False if this disaster has no coordinates or the weather API call failed."
    )


class UnifiedSituationalFeed(BaseSchema):
    """Merged internal + external situational awareness snapshot."""

    disasters: list[DisasterWeatherContext]
    recent_earthquakes: list[EarthquakeEvent]
    earthquakes_available: bool = Field(
        ..., description="False if the USGS feed call failed — list will be empty in that case."
    )
    generated_at: datetime
