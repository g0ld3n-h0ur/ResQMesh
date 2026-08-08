"""
app/models/prediction.py

Prediction model — AI-generated forecasts for disaster scenarios.

The input_features column uses AutoJSON, which stores as JSON on SQLite and
automatically upgrades to native JSONB on PostgreSQL — enabling GIN index
support and containment operators without any application code changes.

Constraints
-----------
- confidence_score  between 0.0 and 1.0 (inclusive)

Indexes
-------
- disaster_id   (predictions per disaster)
- predicted_at  (time-series queries, dashboard charts)
- created_at    (inherited from TimestampMixin via BaseModel)

Relationships
-------------
- disaster → Disaster (many-to-one, required — prediction must link to a disaster)

Loading strategy: lazy="select"
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.types import AutoJSON

if TYPE_CHECKING:
    from app.models.disaster import Disaster


class Prediction(BaseModel):
    """An AI-generated prediction record associated with a disaster event."""

    __tablename__ = "predictions"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    prediction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable prediction text output from the ML model.",
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Model confidence score in range [0.0, 1.0].",
    )
    input_features: Mapped[Optional[Any]] = mapped_column(
        AutoJSON,
        nullable=True,
        doc=(
            "Serialised input feature dictionary fed to the ML model. "
            "Stored as JSON (SQLite) or JSONB (PostgreSQL)."
        ),
    )
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Timestamp when the prediction was generated (UTC).",
    )
    disaster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("disasters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="UUID of the disaster this prediction is associated with.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    disaster: Mapped["Disaster"] = relationship(
        "Disaster",
        back_populates="predictions",
        lazy="select",
        doc="The disaster event this prediction was generated for.",
    )

    # ---------------------------------------------------------------------- #
    # Table constraints and composite indexes                                 #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_prediction_confidence_range",
        ),
        Index("ix_predictions_disaster_predicted_at", "disaster_id", "predicted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} disaster_id={self.disaster_id} "
            f"confidence={self.confidence_score:.2f}>"
        )
