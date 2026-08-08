"""
app/models/hospital.py

Hospital model — medical facility registry with real-time capacity tracking.

Constraints
-----------
- available_beds   >= 0
- icu_beds         >= 0
- ventilators      >= 0
- ambulances       >= 0
- blood_units      >= 0
- oxygen_units     >= 0
- latitude         between -90 and 90
- longitude        between -180 and 180

Relationships
-------------
- assignments → Assignment (one-to-many, via hospital_id)

Loading strategy: lazy="select"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.assignment import Assignment


class Hospital(BaseModel):
    """Medical facility registered in the disaster relief network."""

    __tablename__ = "hospitals"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    hospital_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Official name of the hospital.",
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
    available_beds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of currently available general ward beds.",
    )
    icu_beds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of available ICU beds.",
    )
    ventilators: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of available mechanical ventilators.",
    )
    ambulances: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of operational ambulances.",
    )
    blood_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of available blood units across all types.",
    )
    oxygen_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of available oxygen cylinders/units.",
    )
    contact_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Primary emergency contact number.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="hospital",
        cascade="save-update, merge",
        lazy="select",
        doc="Disaster assignments where this hospital is the assignee.",
    )

    # ---------------------------------------------------------------------- #
    # Table constraints and composite indexes                                 #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_hospital_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_hospital_longitude_range",
        ),
        CheckConstraint("available_beds >= 0", name="ck_hospital_available_beds_non_negative"),
        CheckConstraint("icu_beds >= 0", name="ck_hospital_icu_beds_non_negative"),
        CheckConstraint("ventilators >= 0", name="ck_hospital_ventilators_non_negative"),
        CheckConstraint("ambulances >= 0", name="ck_hospital_ambulances_non_negative"),
        CheckConstraint("blood_units >= 0", name="ck_hospital_blood_units_non_negative"),
        CheckConstraint("oxygen_units >= 0", name="ck_hospital_oxygen_units_non_negative"),
        Index("ix_hospitals_lat_lon", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Hospital id={self.id} name={self.hospital_name!r}>"
