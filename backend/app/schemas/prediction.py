"""
app/schemas/prediction.py

Pydantic v2 schemas for the Prediction model.

Schema hierarchy
----------------
PredictionBase     — shared readable fields
  └── PredictionCreate  — input for POST /predictions
  └── PredictionUpdate  — input for PATCH /predictions/{id}
PredictionResponse — ORM-compatible full response

Validation
----------
- confidence_score: 0.0 ≤ value ≤ 1.0

The input_features field accepts any JSON-serialisable dict, reflecting
the AutoJSON column (JSON on SQLite, JSONB on PostgreSQL).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, FullResponseSchema


class PredictionBase(BaseSchema):
    """Shared readable fields for Prediction."""

    prediction: str = Field(
        ..., min_length=1, description="Human-readable prediction text from the ML model."
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score in range [0.0, 1.0].",
    )
    input_features: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Serialised input feature dictionary used by the ML model. "
            "Stored as JSON (SQLite) or JSONB (PostgreSQL)."
        ),
    )


class PredictionCreate(PredictionBase):
    """Input schema for creating a new AI prediction record."""

    disaster_id: UUID = Field(
        ..., description="UUID of the disaster this prediction is generated for."
    )


class PredictionUpdate(BaseSchema):
    """Partial update schema for PATCH operations."""

    prediction: Optional[str] = Field(None, min_length=1)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    input_features: Optional[dict[str, Any]] = None


class PredictionResponse(FullResponseSchema, PredictionBase):
    """
    ORM-compatible response schema for Prediction.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    disaster_id: UUID = Field(..., description="UUID of the associated disaster.")
    predicted_at: datetime = Field(..., description="Timestamp when the prediction was generated.")
