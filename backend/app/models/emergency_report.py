"""
app/models/emergency_report.py

EmergencyReport model — field incident reports submitted by citizens and responders.

Anonymous reports are supported (reported_by_user_id is nullable), allowing
citizens without accounts to submit reports via the public API.

Constraints
-----------
- latitude  between -90 and 90
- longitude between -180 and 180

Indexes
-------
- reported_at          (time-based dashboard queries)
- reported_by_user_id  (user history)
- linked_disaster_id   (reports per disaster)
- latitude             (geographic filtering)
- longitude            (geographic filtering)

Relationships
-------------
- reported_by_user → User     (many-to-one, nullable — anonymous allowed)
- linked_disaster  → Disaster (many-to-one, nullable — may not yet be verified)

Loading strategy: lazy="select"
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.disaster import Disaster
    from app.models.user import User


class EmergencyReport(BaseModel):
    """A field emergency incident report submitted by a citizen or responder."""

    __tablename__ = "emergency_reports"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    reporter_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Full name of the person submitting this report.",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Contact phone number of the reporter.",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed description of the emergency situation.",
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        doc="Latitude of the incident location (-90 to 90).",
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        doc="Longitude of the incident location (-180 to 180).",
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        doc="URL to an uploaded image documenting the incident.",
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Timestamp when the report was submitted (UTC).",
    )
    # Nullable FK — anonymous reports are permitted
    reported_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the registered user who submitted this report (null if anonymous).",
    )
    # Nullable FK — report may precede verified disaster creation
    linked_disaster_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("disasters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the disaster event this report is associated with.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    reported_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="emergency_reports",
        lazy="select",
        doc="The registered user who submitted this report.",
    )
    linked_disaster: Mapped[Optional["Disaster"]] = relationship(
        "Disaster",
        back_populates="emergency_reports",
        lazy="select",
        doc="The verified disaster event linked to this report.",
    )

    # ---------------------------------------------------------------------- #
    # Table constraints and composite indexes                                 #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_report_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_report_longitude_range",
        ),
        Index("ix_reports_lat_lon", "latitude", "longitude"),
        Index("ix_reports_disaster_reported_at", "linked_disaster_id", "reported_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmergencyReport id={self.id} reporter={self.reporter_name!r} "
            f"reported_at={self.reported_at}>"
        )
