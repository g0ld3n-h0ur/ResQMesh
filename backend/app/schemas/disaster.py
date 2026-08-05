"""
app/schemas/disaster.py

Pydantic v2 schemas for the Disaster model.

Schema hierarchy
----------------
DisasterBase     — shared readable fields
  └── DisasterCreate  — input schema for POST /disasters
  └── DisasterUpdate  — input schema for PATCH /disasters/{id}
DisasterResponse — ORM-compatible full response schema

Validation
----------
- latitude:  -90.0 ≤ value ≤ 90.0
- longitude: -180.0 ≤ value ≤ 180.0
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import DisasterSeverity, DisasterStatus
from app.schemas.base import BaseSchema, FullResponseSchema


class DisasterBase(BaseSchema):
    """Shared readable fields for Disaster."""

    title: str = Field(..., min_length=1, max_length=255, description="Short disaster title.")
    description: Optional[str] = Field(None, description="Detailed situation description.")
    disaster_type: str = Field(
        ..., max_length=100, description="Type (e.g. 'flood', 'earthquake', 'cyclone')."
    )
    severity: DisasterSeverity = Field(..., description="Assessed severity level.")
    status: DisasterStatus = Field(
        DisasterStatus.REPORTED, description="Current lifecycle status."
    )
    latitude: Optional[float] = Field(None, description="Epicentre latitude (-90 to 90).")
    longitude: Optional[float] = Field(None, description="Epicentre longitude (-180 to 180).")
    district: Optional[str] = Field(None, max_length=100, description="Administrative district.")
    state: Optional[str] = Field(None, max_length=100, description="State or province.")
    country: Optional[str] = Field("India", max_length=100, description="Country.")

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


class DisasterCreate(DisasterBase):
    """Input schema for creating a new disaster record."""

    reported_by: Optional[UUID] = Field(
        None, description="UUID of the user reporting this disaster."
    )


class DisasterUpdate(BaseSchema):
    """Partial update schema for PATCH operations."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    disaster_type: Optional[str] = Field(None, max_length=100)
    severity: Optional[DisasterSeverity] = None
    status: Optional[DisasterStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

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


class DisasterResponse(FullResponseSchema, DisasterBase):
    """
    ORM-compatible response schema for Disaster.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    reported_by: Optional[UUID] = Field(None, description="UUID of the reporting user.")
