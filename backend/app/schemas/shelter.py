"""
app/schemas/shelter.py

Pydantic v2 schemas for the Shelter model.

Schema hierarchy
----------------
ShelterBase     — shared readable fields
  └── ShelterCreate  — input for POST /shelters
  └── ShelterUpdate  — input for PATCH /shelters/{id}
ShelterResponse — ORM-compatible full response

Validation
----------
- latitude:           -90.0 ≤ value ≤ 90.0
- longitude:          -180.0 ≤ value ≤ 180.0
- capacity:           >= 0
- current_occupancy:  >= 0 and <= capacity (cross-field)
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, FullResponseSchema


class ShelterBase(BaseSchema):
    """Shared readable fields for Shelter."""

    shelter_name: str = Field(
        ..., min_length=1, max_length=255, description="Name or identifier of the shelter."
    )
    latitude: Optional[float] = Field(None, description="Geographic latitude (-90 to 90).")
    longitude: Optional[float] = Field(None, description="Geographic longitude (-180 to 180).")
    capacity: int = Field(0, ge=0, description="Maximum evacuee capacity.")
    current_occupancy: int = Field(0, ge=0, description="Current number of evacuees housed.")
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

    @model_validator(mode="after")
    def occupancy_within_capacity(self) -> "ShelterBase":
        if self.current_occupancy > self.capacity:
            raise ValueError("current_occupancy cannot exceed capacity.")
        return self


class ShelterCreate(ShelterBase):
    """Input schema for registering a new shelter facility."""

    pass


class ShelterUpdate(BaseSchema):
    """Partial update schema for PATCH operations."""

    shelter_name: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = Field(None, ge=0)
    current_occupancy: Optional[int] = Field(None, ge=0)
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


class ShelterResponse(FullResponseSchema, ShelterBase):
    """
    ORM-compatible response schema for Shelter.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    @property
    def available_capacity(self) -> int:
        """Computed available capacity = capacity - current_occupancy."""
        return max(0, self.capacity - self.current_occupancy)
