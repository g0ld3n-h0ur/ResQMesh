"""
app/schemas/allocation_suggestion.py

Pydantic v2 schema for a single suggested resource allocation line item.
See app/services/allocation_service.py for the optimization algorithm.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class AllocationSuggestionItem(BaseSchema):
    """One suggested (resource_id -> disaster_id, quantity) allocation."""

    resource_id: UUID
    resource_type: str
    resource_location: str | None = None
    source_available_quantity: int = Field(
        ..., description="Total unassigned quantity currently available on this resource row."
    )

    disaster_id: UUID
    disaster_title: str
    disaster_need_rank: int
    disaster_need_score: float

    suggested_quantity: int = Field(..., ge=1)
    rationale: str
