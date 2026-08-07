"""
app/schemas/need_score.py

Pydantic v2 schemas for the computed disaster need/severity score.

See app/services/need_score_service.py for the scoring formula itself —
these schemas only describe its output shape.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.enums import DisasterSeverity, DisasterStatus
from app.schemas.base import BaseSchema


class NeedScoreBreakdown(BaseSchema):
    """The four weighted components that sum to the overall need_score."""

    severity_component: float = Field(
        ..., description="Contribution from the government-assessed severity level (weight 0.35)."
    )
    report_pressure_component: float = Field(
        ..., description="Contribution from citizen-reported incident volume (weight 0.30)."
    )
    resource_shortfall_component: float = Field(
        ..., description="Contribution from unmet/depleted resource assignments (weight 0.25)."
    )
    status_urgency_component: float = Field(
        ..., description="Contribution from how early/stalled the response lifecycle is (weight 0.10)."
    )


class NeedScoreResponse(BaseSchema):
    """A single disaster's computed need score, ranked against its peers."""

    disaster_id: UUID
    title: str
    disaster_type: str
    severity: DisasterSeverity
    status: DisasterStatus
    district: str | None = None
    state: str | None = None
    report_count: int = Field(..., description="Number of emergency reports linked to this disaster.")
    resources_assigned: int = Field(..., description="Number of resource records assigned to this disaster.")
    need_score: float = Field(..., ge=0, le=100, description="Composite computed need score, 0-100.")
    need_level: str = Field(..., description="Bucketed label derived from need_score: low | medium | high | critical.")
    rank: int = Field(..., description="1-indexed rank among returned disasters, highest need first.")
    breakdown: NeedScoreBreakdown
