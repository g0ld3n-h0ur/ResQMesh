"""
app/models/shelter.py

Shelter model — emergency shelter facility registry and occupancy tracking.

Constraints
-----------
- capacity          >= 0
- current_occupancy >= 0
- current_occupancy <= capacity  (enforced at DB level via CheckConstraint)
- latitude          between -90 and 90
- longitude         between -180 and 180

No outgoing foreign keys. Shelter is a standalone resource entity.
Future phases may introduce Assignment → Shelter linkage.

Loading strategy: no relationships (standalone model)
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import CheckConstraint, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Shelter(BaseModel):
    """Emergency shelter facility registered in the disaster relief network."""

    __tablename__ = "shelters"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    shelter_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Official name or identifier of the shelter.",
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        doc="Geographic latitude (-90 to 90).",
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
        doc="Geographic longitude (-180 to 180).",
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Maximum number of evacuees the shelter can accommodate.",
    )
    current_occupancy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of evacuees currently housed at this shelter.",
    )
    contact_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Primary emergency contact number for the shelter.",
    )

    # ---------------------------------------------------------------------- #
    # Table constraints and composite indexes                                 #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_shelter_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_shelter_longitude_range",
        ),
        CheckConstraint("capacity >= 0", name="ck_shelter_capacity_non_negative"),
        CheckConstraint(
            "current_occupancy >= 0", name="ck_shelter_current_occupancy_non_negative"
        ),
        CheckConstraint(
            "current_occupancy <= capacity",
            name="ck_shelter_occupancy_within_capacity",
        ),
        Index("ix_shelters_lat_lon", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return (
            f"<Shelter id={self.id} name={self.shelter_name!r} "
            f"occupancy={self.current_occupancy}/{self.capacity}>"
        )
