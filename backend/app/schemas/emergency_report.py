"""
app/schemas/emergency_report.py

Pydantic v2 schemas for the EmergencyReport model.

Schema hierarchy
----------------
EmergencyReportBase     — shared readable fields
  └── EmergencyReportCreate  — input for POST /reports
  └── EmergencyReportUpdate  — input for PATCH /reports/{id}
EmergencyReportResponse — ORM-compatible full response

Validation
----------
- latitude:  -90.0 ≤ value ≤ 90.0
- longitude: -180.0 ≤ value ≤ 180.0
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, FullResponseSchema


class EmergencyReportBase(BaseSchema):
    """Shared readable fields for EmergencyReport."""

    reporter_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the person submitting the report."
    )
    phone: Optional[str] = Field(None, max_length=20, description="Reporter contact number.")
    description: str = Field(..., min_length=1, description="Description of the emergency.")
    latitude: Optional[float] = Field(None, description="Incident latitude (-90 to 90).")
    longitude: Optional[float] = Field(None, description="Incident longitude (-180 to 180).")
    image_url: Optional[str] = Field(
        None, max_length=1024, description="URL of an uploaded incident image."
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


class EmergencyReportCreate(EmergencyReportBase):
    """Input schema for submitting a new emergency report."""

    reported_by_user_id: Optional[UUID] = Field(
        None, description="UUID of the submitting user (null for anonymous reports)."
    )
    linked_disaster_id: Optional[UUID] = Field(
        None, description="UUID of an existing disaster to link this report to."
    )


class EmergencyReportUpdate(BaseSchema):
    """Partial update schema for PATCH operations."""

    description: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = Field(None, max_length=1024)
    linked_disaster_id: Optional[UUID] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

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


class EmergencyReportResponse(FullResponseSchema, EmergencyReportBase):
    """
    ORM-compatible response schema for EmergencyReport.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    reported_at: datetime = Field(..., description="Timestamp when the report was submitted.")
    reported_by_user_id: Optional[UUID] = Field(None, description="Submitting user UUID.")
    linked_disaster_id: Optional[UUID] = Field(None, description="Linked disaster UUID.")
