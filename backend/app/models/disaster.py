"""
app/models/disaster.py

Disaster model — the central aggregation entity of the entire platform.

All response coordination (resources, predictions, assignments, reports)
is anchored to a Disaster record via foreign keys.

Constraints
-----------
- latitude   between -90 and 90
- longitude  between -180 and 180

Indexes
-------
- severity    (filter by criticality)
- status      (filter by lifecycle stage)
- district    (geographic dashboard queries)
- latitude    (proximity calculations)
- longitude   (proximity calculations)
- severity+status  (composite — common dashboard filter)
- district+status  (composite — geographic + lifecycle filter)
- latitude+longitude (composite — bounding-box map queries)

Relationships
-------------
- reporter         → User          (many-to-one, via reported_by FK)
- predictions      → Prediction    (one-to-many, cascade delete)
- resources        → Resource      (one-to-many, via assigned_disaster FK)
- emergency_reports → EmergencyReport (one-to-many)
- assignments      → Assignment    (one-to-many, cascade delete)

Loading strategy: lazy="select"
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import DisasterSeverity, DisasterStatus

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.emergency_report import EmergencyReport
    from app.models.prediction import Prediction
    from app.models.resource import Resource
    from app.models.user import User


class Disaster(BaseModel):
    """A disaster event — the core entity of the platform."""

    __tablename__ = "disasters"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Short descriptive title of the disaster event.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the disaster, its impact, and context.",
    )
    disaster_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of disaster (e.g. 'flood', 'earthquake', 'cyclone').",
    )
    severity: Mapped[DisasterSeverity] = mapped_column(
        SAEnum(
            DisasterSeverity,
            name="disaster_severity",
            create_constraint=True,
            native_enum=False,
        ),
        nullable=False,
        index=True,
        doc="Assessed severity level of the disaster.",
    )
    status: Mapped[DisasterStatus] = mapped_column(
        SAEnum(
            DisasterStatus,
            name="disaster_status",
            create_constraint=True,
            native_enum=False,
        ),
        nullable=False,
        default=DisasterStatus.REPORTED,
        index=True,
        doc="Current lifecycle status of the disaster response.",
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        doc="Geographic latitude of the disaster epicentre (-90 to 90).",
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        doc="Geographic longitude of the disaster epicentre (-180 to 180).",
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Administrative district where the disaster occurred.",
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="State or province of the disaster location.",
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="India",
        doc="Country of the disaster. Defaults to India.",
    )
    reported_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the user who originally reported this disaster.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    reporter: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reported_disasters",
        lazy="select",
        doc="User who originally reported this disaster.",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction",
        back_populates="disaster",
        cascade="all, delete-orphan",
        lazy="select",
        doc="AI-generated predictions associated with this disaster.",
    )
    resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="disaster",
        cascade="save-update, merge",
        lazy="select",
        foreign_keys="[Resource.assigned_disaster]",
        doc="Relief resources currently assigned to this disaster.",
    )
    emergency_reports: Mapped[list["EmergencyReport"]] = relationship(
        "EmergencyReport",
        back_populates="linked_disaster",
        cascade="save-update, merge",
        lazy="select",
        doc="Field emergency reports linked to this disaster.",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="disaster",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Volunteer, NGO, resource, and hospital assignments for this disaster.",
    )

    # ---------------------------------------------------------------------- #
    # Table constraints and composite indexes                                 #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_disaster_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_disaster_longitude_range",
        ),
        Index("ix_disasters_severity_status", "severity", "status"),
        Index("ix_disasters_district_status", "district", "status"),
        Index("ix_disasters_lat_lon", "latitude", "longitude"),
        Index("ix_disasters_type_severity", "disaster_type", "severity"),
    )

    def __repr__(self) -> str:
        return (
            f"<Disaster id={self.id} title={self.title!r} "
            f"severity={self.severity} status={self.status}>"
        )
