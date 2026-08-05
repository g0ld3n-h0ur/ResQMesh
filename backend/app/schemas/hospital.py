"""
app/schemas/hospital.py

Pydantic v2 schemas for the Hospital model.

Schema hierarchy
----------------
HospitalBase         — shared readable fields
  └── HospitalCreate — input for POST /hospitals              (Government)
  └── HospitalUpdate — input for PUT /hospitals/{id}          (Gov + Hospital)
AvailabilityUpdate   — input for PATCH /hospitals/{id}/availability
HospitalResponse     — ORM-compatible full response

Validation
----------
- latitude:           -90.0 ≤ value ≤ 90.0
- longitude:          -180.0 ≤ value ≤ 180.0
- available_beds:     >= 0
- icu_beds:           >= 0
- ventilators:        >= 0
- ambulances:         >= 0
- blood_units:        >= 0
- oxygen_units:       >= 0
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, FullResponseSchema


class HospitalBase(BaseSchema):
    """Shared readable fields for Hospital."""

    hospital_name: str = Field(
        ..., min_length=1, max_length=255, description="Official name of the hospital."
    )
    latitude: Optional[float] = Field(None, description="Geographic latitude (-90 to 90).")
    longitude: Optional[float] = Field(None, description="Geographic longitude (-180 to 180).")
    available_beds: int = Field(0, ge=0, description="Number of available general ward beds.")
    icu_beds: int = Field(0, ge=0, description="Number of available ICU beds.")
    ventilators: int = Field(0, ge=0, description="Number of available mechanical ventilators.")
    ambulances: int = Field(0, ge=0, description="Number of operational ambulances.")
    blood_units: int = Field(0, ge=0, description="Number of available blood units.")
    oxygen_units: int = Field(0, ge=0, description="Number of available oxygen cylinders/units.")
    contact_number: Optional[str] = Field(
        None, max_length=20, description="Primary emergency contact number."
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90 and 90.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180 and 180.")
        return v


class HospitalCreate(HospitalBase):
    """Input schema for registering a new hospital (Government only)."""

    pass


class HospitalUpdate(BaseSchema):
    """
    Partial update schema for PUT /hospitals/{id}.

    All fields are optional — only provided fields are applied.
    """

    hospital_name: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    available_beds: Optional[int] = Field(None, ge=0)
    icu_beds: Optional[int] = Field(None, ge=0)
    ventilators: Optional[int] = Field(None, ge=0)
    ambulances: Optional[int] = Field(None, ge=0)
    blood_units: Optional[int] = Field(None, ge=0)
    oxygen_units: Optional[int] = Field(None, ge=0)
    contact_number: Optional[str] = Field(None, max_length=20)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90 and 90.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180 and 180.")
        return v


class AvailabilityUpdate(BaseSchema):
    """
    Targeted capacity update for PATCH /hospitals/{id}/availability.

    Designed for real-time field reporting of bed counts, equipment
    availability, and supply levels.  At least one field must be provided
    (enforced by the service layer).  All values must be >= 0.
    """

    available_beds: Optional[int] = Field(
        None, ge=0, description="Updated count of available general ward beds."
    )
    icu_beds: Optional[int] = Field(
        None, ge=0, description="Updated count of available ICU beds."
    )
    ventilators: Optional[int] = Field(
        None, ge=0, description="Updated count of available mechanical ventilators."
    )
    ambulances: Optional[int] = Field(
        None, ge=0, description="Updated count of operational ambulances."
    )
    blood_units: Optional[int] = Field(
        None, ge=0, description="Updated count of available blood units."
    )
    oxygen_units: Optional[int] = Field(
        None, ge=0, description="Updated count of available oxygen cylinders/units."
    )


class HospitalResponse(FullResponseSchema, HospitalBase):
    """
    ORM-compatible response schema for Hospital.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    Inherits all capacity fields from HospitalBase.
    """

    pass
