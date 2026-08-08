"""
app/models/resource.py

Resource model — relief inventory items (food, water, medicine, equipment, etc.).

Constraints
-----------
- quantity           >= 0
- available_quantity >= 0
- available_quantity <= quantity  (enforced at DB level)

Relationships
-------------
- disaster    → Disaster    (many-to-one, via assigned_disaster FK)
- assignments → Assignment  (one-to-many, via resource_id)

Loading strategy: lazy="select"
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Enum as SAEnum, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import ResourceStatus

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.disaster import Disaster


class Resource(BaseModel):
    """A relief resource item tracked in the platform inventory."""

    __tablename__ = "resources"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Category of resource (e.g. 'food', 'water', 'medical_kit').",
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total quantity of this resource in stock.",
    )
    available_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Quantity currently available for allocation.",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Physical storage location or depot name.",
    )
    status: Mapped[ResourceStatus] = mapped_column(
        SAEnum(ResourceStatus, name="resource_status", create_constraint=True, native_enum=False),
        nullable=False,
        default=ResourceStatus.AVAILABLE,
        index=True,
        doc="Current operational status of this resource.",
    )
    # FK column named as per spec: assigned_disaster
    assigned_disaster: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("disasters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of the disaster this resource is currently assigned to.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    disaster: Mapped[Optional["Disaster"]] = relationship(
        "Disaster",
        back_populates="resources",
        lazy="select",
        doc="The disaster event this resource is allocated to.",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="resource",
        cascade="save-update, merge",
        lazy="select",
        doc="Assignment records linking this resource to response operations.",
    )

    # ---------------------------------------------------------------------- #
    # Table constraints and composite indexes                                 #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_resource_quantity_non_negative"),
        CheckConstraint(
            "available_quantity >= 0", name="ck_resource_available_quantity_non_negative"
        ),
        CheckConstraint(
            "available_quantity <= quantity",
            name="ck_resource_available_lte_total",
        ),
        Index("ix_resources_type_status", "resource_type", "status"),
        Index("ix_resources_status_disaster", "status", "assigned_disaster"),
    )

    def __repr__(self) -> str:
        return (
            f"<Resource id={self.id} type={self.resource_type!r} "
            f"qty={self.available_quantity}/{self.quantity} status={self.status}>"
        )
