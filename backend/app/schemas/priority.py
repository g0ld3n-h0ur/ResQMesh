"""
app/schemas/priority.py

Pydantic v2 schemas for the urgency + accessibility distribution priority
ranking. See app/services/priority_service.py for the scoring formula.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.enums import DisasterSeverity, DisasterStatus
from app.schemas.base import BaseSchema


class DistributionPriorityResponse(BaseSchema):
    """A single disaster's combined urgency + accessibility distribution priority."""

    disaster_id: UUID
    title: str
    disaster_type: str
    severity: DisasterSeverity
    status: DisasterStatus
    district: str | None = None
    state: str | None = None

    need_score: float = Field(..., description="Urgency component — see /disasters/need-scores.")

    nearest_shelter_name: str | None = None
    nearest_shelter_distance_km: float | None = None
    nearest_hospital_name: str | None = None
    nearest_hospital_distance_km: float | None = None

    accessibility_score: float = Field(
        ..., ge=0, le=100,
        description="0-100, higher = closer to responder assets (shelters/hospitals). "
        "50 (neutral) when coordinates are unavailable for this disaster or all assets.",
    )
    accessibility_data_available: bool = Field(
        ..., description="False if the disaster or all candidate assets lack lat/long."
    )

    distribution_priority_score: float = Field(
        ..., ge=0, le=100,
        description="0.6 * need_score + 0.4 * accessibility_score. "
        "Ranks disasters that are both urgent AND currently reachable highest, "
        "so limited resources go where they'll have the fastest, most certain impact.",
    )
    rank: int
