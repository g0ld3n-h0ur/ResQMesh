"""
app/schemas/patch.py

Targeted PATCH-operation request schemas.

These cover partial updates that are not expressible via the standard
*Update schemas (e.g. single-field state transitions, delta-based
occupancy changes, or composite availability updates).

All schemas inherit from BaseSchema (from_attributes=True, use_enum_values=True).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import AssignmentStatus, DisasterSeverity, DisasterStatus
from app.schemas.base import BaseSchema


class SeverityPatch(BaseSchema):
    """PATCH body for updating a disaster's severity level."""

    severity: DisasterSeverity = Field(
        ...,
        description="New severity level to assign to the disaster.",
    )


class DisasterStatusPatch(BaseSchema):
    """PATCH body for updating a disaster's lifecycle status."""

    status: DisasterStatus = Field(
        ...,
        description="New operational status for the disaster response.",
    )


class VerifyReportPatch(BaseSchema):
    """PATCH body for verifying an emergency report."""

    linked_disaster_id: Optional[UUID] = Field(
        None,
        description=(
            "UUID of the disaster event to link this report to. "
            "Null leaves the report linked but unassociated."
        ),
    )


class AllocateResourcePatch(BaseSchema):
    """PATCH body for allocating a resource to a disaster."""

    disaster_id: UUID = Field(
        ...,
        description="UUID of the disaster to allocate this resource to.",
    )
    quantity: Optional[int] = Field(
        None,
        ge=1,
        description=(
            "Quantity to mark as allocated. "
            "Defaults to all currently available_quantity."
        ),
    )


class HospitalAvailabilityPatch(BaseSchema):
    """
    PATCH body for updating hospital resource availability.

    All fields are optional — send only the fields that have changed.
    All values must be >= 0.
    """

    available_beds: Optional[int] = Field(None, ge=0, description="General ward beds available.")
    icu_beds: Optional[int] = Field(None, ge=0, description="ICU beds available.")
    ventilators: Optional[int] = Field(None, ge=0, description="Ventilators available.")
    ambulances: Optional[int] = Field(None, ge=0, description="Operational ambulances.")
    blood_units: Optional[int] = Field(None, ge=0, description="Blood units in stock.")
    oxygen_units: Optional[int] = Field(None, ge=0, description="Oxygen cylinders available.")

    @model_validator(mode="after")
    def at_least_one_field(self) -> "HospitalAvailabilityPatch":
        fields = [
            self.available_beds, self.icu_beds, self.ventilators,
            self.ambulances, self.blood_units, self.oxygen_units,
        ]
        if all(v is None for v in fields):
            raise ValueError(
                "At least one availability field must be provided."
            )
        return self


class OccupancyPatch(BaseSchema):
    """
    PATCH body for updating shelter occupancy.

    delta > 0 = check-in N people (increases current_occupancy).
    delta < 0 = check-out N people (decreases current_occupancy).
    delta cannot be zero.
    """

    delta: int = Field(
        ...,
        description=(
            "People to add (positive) or remove (negative) from shelter. "
            "E.g. 50 = check in 50, -30 = check out 30."
        ),
    )

    @model_validator(mode="after")
    def delta_not_zero(self) -> "OccupancyPatch":
        if self.delta == 0:
            raise ValueError("delta cannot be zero.")
        return self


class AssignmentStatusPatch(BaseSchema):
    """PATCH body for updating an assignment's lifecycle status."""

    status: AssignmentStatus = Field(
        ...,
        description="New assignment lifecycle status.",
    )
