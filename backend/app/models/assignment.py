"""
app/models/assignment.py

Assignment model — links volunteers, NGOs, hospitals, and resources to disasters.

Multiple nullable FK columns allow flexible many-to-many-style assignment:
  - A single assignment may involve a resource, a volunteer, an NGO, or a hospital.
  - Only disaster_id is mandatory.
  - All other FK columns are nullable to support partial assignments.

Ambiguity resolution for multiple User FKs
-------------------------------------------
Assignment has two FK columns pointing to users.id:
  - volunteer_id  (User acting as a volunteer)
  - ngo_id        (User acting as an NGO representative)

SQLAlchemy requires explicit primaryjoin expressions for both relationships
to avoid AmbiguousForeignKeysError at mapper configuration time.

Indexes
-------
- disaster_id    (assignments per disaster)
- volunteer_id   (assignments per volunteer)
- ngo_id         (assignments per NGO)
- resource_id    (assignments per resource)
- hospital_id    (assignments per hospital)
- status         (filter by lifecycle stage)
- disaster_id+status (composite — common dashboard query)

Relationships
-------------
- resource  → Resource  (many-to-one, nullable)
- volunteer → User      (many-to-one, via volunteer_id, nullable)
- ngo       → User      (many-to-one, via ngo_id, nullable)
- hospital  → Hospital  (many-to-one, nullable)
- disaster  → Disaster  (many-to-one, required)

Loading strategy: lazy="select"
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import AssignmentStatus

if TYPE_CHECKING:
    from app.models.disaster import Disaster
    from app.models.hospital import Hospital
    from app.models.resource import Resource
    from app.models.user import User


class Assignment(BaseModel):
    """Assignment record linking response actors to a disaster event."""

    __tablename__ = "assignments"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the resource assigned (null if not resource-based).",
    )
    volunteer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the volunteer user assigned (null if not volunteer-based).",
    )
    ngo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the NGO user assigned (null if not NGO-based).",
    )
    hospital_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the hospital assigned (null if not hospital-based).",
    )
    disaster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("disasters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="UUID of the disaster this assignment belongs to. Required.",
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(
            AssignmentStatus,
            name="assignment_status",
            create_constraint=True,
            native_enum=False,
        ),
        nullable=False,
        default=AssignmentStatus.PENDING,
        index=True,
        doc="Current lifecycle status of this assignment.",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when this assignment was created (UTC).",
    )

    # ---------------------------------------------------------------------- #
    # Relationships — explicit primaryjoin required for multiple User FKs    #
    # ---------------------------------------------------------------------- #
    resource: Mapped[Optional["Resource"]] = relationship(
        "Resource",
        back_populates="assignments",
        lazy="select",
        doc="The resource involved in this assignment.",
    )
    volunteer: Mapped[Optional["User"]] = relationship(
        "User",
        primaryjoin="Assignment.volunteer_id == User.id",
        foreign_keys="[Assignment.volunteer_id]",
        back_populates="assignments",
        lazy="select",
        doc="The volunteer user assigned in this record.",
    )
    ngo: Mapped[Optional["User"]] = relationship(
        "User",
        primaryjoin="Assignment.ngo_id == User.id",
        foreign_keys="[Assignment.ngo_id]",
        back_populates="ngo_assignments",
        lazy="select",
        doc="The NGO user assigned in this record.",
    )
    hospital: Mapped[Optional["Hospital"]] = relationship(
        "Hospital",
        back_populates="assignments",
        lazy="select",
        doc="The hospital assigned in this record.",
    )
    disaster: Mapped["Disaster"] = relationship(
        "Disaster",
        back_populates="assignments",
        lazy="select",
        doc="The disaster event this assignment is part of.",
    )

    # ---------------------------------------------------------------------- #
    # Composite indexes                                                       #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        Index("ix_assignments_disaster_status", "disaster_id", "status"),
        Index("ix_assignments_volunteer_status", "volunteer_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Assignment id={self.id} disaster_id={self.disaster_id} "
            f"status={self.status}>"
        )
