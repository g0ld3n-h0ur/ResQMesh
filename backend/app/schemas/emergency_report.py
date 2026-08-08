"""
app/schemas/emergency_report.py

Pydantic v2 schemas for the EmergencyReport model.

Schema hierarchy
----------------
EmergencyReportBase          — shared readable fields
  └── EmergencyReportCreate  — input for POST /reports/emergency (public)
EmergencyReportVerify        — input for PATCH /reports/{id}/verify (government)
EmergencyReportResponse      — ORM-compatible full response
EmergencyReportListResponse  — paginated list wrapper item
ReportVerifyRequest          — body for verify PATCH endpoint

Validation
----------
- reporter_name : required, 1–255 chars
- phone         : optional, E.164-compatible, max 20 chars
- description   : required, min 1 char
- latitude      : optional, -90.0 ≤ value ≤ 90.0
- longitude     : optional, -180.0 ≤ value ≤ 180.0
- disaster_type : optional free-text classification
- address       : optional human-readable location string
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, FullResponseSchema

# ---------------------------------------------------------------------------
# Compiled regex for basic phone validation (E.164 or local formats)
# ---------------------------------------------------------------------------
_PHONE_PATTERN = re.compile(r"^\+?[\d\s\-().]{7,20}$")


# ---------------------------------------------------------------------------
# Base — shared readable fields
# ---------------------------------------------------------------------------


class EmergencyReportBase(BaseSchema):
    """Shared readable fields for EmergencyReport."""

    reporter_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the person submitting the report.",
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description=(
            "Contact phone number of the reporter. "
            "Accepts E.164 (+91XXXXXXXXXX) or local formats."
        ),
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Detailed description of the emergency situation.",
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Incident latitude (-90.0 to 90.0).",
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Incident longitude (-180.0 to 180.0).",
    )
    image_url: Optional[str] = Field(
        None,
        max_length=1024,
        description="URL of an uploaded image documenting the incident.",
    )
    disaster_type: Optional[str] = Field(
        None,
        max_length=100,
        description=(
            "Type/category of the emergency, e.g. 'flood', 'earthquake', 'fire'."
        ),
    )
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Human-readable address or landmark of the incident location.",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not _PHONE_PATTERN.match(stripped):
            raise ValueError(
                "Phone number must be between 7 and 20 characters and contain only "
                "digits, spaces, hyphens, parentheses, dots, or a leading '+'."
            )
        return stripped

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0.")
        return v

    @model_validator(mode="after")
    def validate_coordinates_pair(self) -> "EmergencyReportBase":
        """Ensure latitude and longitude are both provided or both absent."""
        lat, lon = self.latitude, self.longitude
        if (lat is None) != (lon is None):
            raise ValueError(
                "Latitude and longitude must both be provided together, "
                "or both omitted."
            )
        return self


# ---------------------------------------------------------------------------
# Create — public submission (no auth required)
# ---------------------------------------------------------------------------


class EmergencyReportCreate(EmergencyReportBase):
    """
    Input schema for submitting a new emergency report.

    Used by POST /api/v1/reports/emergency — no authentication required.
    The reported_by_user_id and linked_disaster_id are always null for
    public submissions and are assigned server-side only.
    """

    pass


# ---------------------------------------------------------------------------
# Verify — government action to link/verify a report
# ---------------------------------------------------------------------------


class ReportVerifyRequest(BaseSchema):
    """
    Optional request body for PATCH /api/v1/reports/{id}/verify.

    Government users may optionally link the verified report to an existing
    disaster event. Omit disaster_id to verify without linking.
    """

    disaster_id: Optional[UUID] = Field(
        None,
        description=(
            "UUID of an existing disaster to link this report to. "
            "If omitted the report is marked verified without a disaster link."
        ),
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional verification notes or remarks from the Government officer.",
    )


# ---------------------------------------------------------------------------
# Response — full ORM-mapped response
# ---------------------------------------------------------------------------


class EmergencyReportResponse(FullResponseSchema, EmergencyReportBase):
    """
    ORM-compatible response schema for EmergencyReport.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    Inherits all base report fields from EmergencyReportBase.
    """

    reported_at: datetime = Field(
        ...,
        description="UTC timestamp when the report was submitted.",
    )
    reported_by_user_id: Optional[UUID] = Field(
        None,
        description="UUID of the registered user who submitted this report (null for anonymous).",
    )
    linked_disaster_id: Optional[UUID] = Field(
        None,
        description=(
            "UUID of the disaster event this report is associated with. "
            "Non-null indicates the report has been government-verified."
        ),
    )
    is_verified: bool = Field(
        default=False,
        description=(
            "True when a Government officer has verified this report "
            "(indicated by a linked_disaster_id being set)."
        ),
    )

    @model_validator(mode="after")
    def compute_is_verified(self) -> "EmergencyReportResponse":
        """Derive is_verified from linked_disaster_id presence."""
        self.is_verified = self.linked_disaster_id is not None
        return self


# ---------------------------------------------------------------------------
# Update — partial update schema (used by other services if needed)
# ---------------------------------------------------------------------------


class EmergencyReportUpdate(BaseSchema):
    """
    Partial update schema for PATCH operations on emergency reports.

    All fields are optional — only provided fields are applied.
    Latitude and longitude must be updated together.
    """

    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    image_url: Optional[str] = Field(None, max_length=1024)
    disaster_type: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    linked_disaster_id: Optional[UUID] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0.")
        return v
