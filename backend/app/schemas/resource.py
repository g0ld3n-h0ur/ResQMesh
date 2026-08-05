"""
app/schemas/resource.py

Pydantic v2 schemas for the Resource model.

Schema hierarchy
----------------
ResourceBase     — shared readable fields
  └── ResourceCreate  — input for POST /resources
  └── ResourceUpdate  — input for PATCH /resources/{id}
ResourceResponse — ORM-compatible full response

Validation
----------
- quantity           >= 0
- available_quantity >= 0
- available_quantity <= quantity (cross-field)
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import ResourceStatus
from app.schemas.base import BaseSchema, FullResponseSchema


class ResourceBase(BaseSchema):
    """Shared readable fields for Resource."""

    resource_type: str = Field(
        ..., max_length=100, description="Category (e.g. 'food', 'water', 'medical_kit')."
    )
    quantity: int = Field(..., ge=0, description="Total quantity in stock.")
    available_quantity: int = Field(..., ge=0, description="Quantity available for allocation.")
    location: Optional[str] = Field(
        None, max_length=255, description="Physical storage location or depot name."
    )
    status: ResourceStatus = Field(ResourceStatus.AVAILABLE, description="Operational status.")

    @model_validator(mode="after")
    def available_must_not_exceed_total(self) -> "ResourceBase":
        if self.available_quantity > self.quantity:
            raise ValueError("available_quantity cannot exceed total quantity.")
        return self


class ResourceCreate(ResourceBase):
    """Input schema for creating a new resource record."""

    assigned_disaster: Optional[UUID] = Field(
        None, description="UUID of the disaster to assign this resource to."
    )


class ResourceUpdate(BaseSchema):
    """Partial update schema for PATCH operations."""

    resource_type: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    available_quantity: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[ResourceStatus] = None
    assigned_disaster: Optional[UUID] = None


class ResourceResponse(FullResponseSchema, ResourceBase):
    """
    ORM-compatible response schema for Resource.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    assigned_disaster: Optional[UUID] = Field(
        None, description="UUID of the assigned disaster (null if unallocated)."
    )
