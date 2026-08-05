"""
app/schemas/resource.py

Pydantic v2 schemas for the Resource model.

Schema hierarchy
----------------
ResourceBase          — shared readable fields
  └── ResourceCreate  — input for POST /resources           (Government)
  └── ResourceUpdate  — input for PUT /resources/{id}       (Government)
ResourceResponse      — ORM-compatible full response
AllocateRequest       — body for PATCH /resources/{id}/allocate
ReleaseRequest        — body for PATCH /resources/{id}/release

Validation
----------
- quantity           >= 0
- available_quantity >= 0
- available_quantity <= quantity (cross-field model_validator on create)

Supported resource_type values (enforced by the service layer)
--------------------------------------------------------------
food | water | medicine | blankets | vehicles | fuel | medical_kit | generator
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
        ...,
        max_length=100,
        description=(
            "Category of relief resource. "
            "Accepted values: food | water | medicine | blankets | "
            "vehicles | fuel | medical_kit | generator."
        ),
    )
    quantity: int = Field(..., ge=0, description="Total quantity of this resource in stock.")
    available_quantity: int = Field(
        ..., ge=0, description="Quantity currently available for allocation."
    )
    location: Optional[str] = Field(
        None, max_length=255, description="Physical storage location or depot name."
    )
    status: ResourceStatus = Field(
        ResourceStatus.AVAILABLE,
        description=(
            "Operational status: available | allocated | in_transit | consumed."
        ),
    )

    @model_validator(mode="after")
    def available_must_not_exceed_total(self) -> "ResourceBase":
        if self.available_quantity > self.quantity:
            raise ValueError(
                f"available_quantity ({self.available_quantity}) cannot exceed "
                f"total quantity ({self.quantity})."
            )
        return self


class ResourceCreate(ResourceBase):
    """Input schema for creating a new resource record (Government only)."""

    assigned_disaster: Optional[UUID] = Field(
        None,
        description="UUID of the disaster to immediately assign this resource to.",
    )


class ResourceUpdate(BaseSchema):
    """
    Partial update schema for PUT /resources/{id} (Government only).

    All fields are optional — only provided fields are applied.
    The service layer performs cross-field quantity validation after merging
    provided values with the existing record.
    """

    resource_type: Optional[str] = Field(
        None,
        max_length=100,
        description="New resource category (service validates allowed values).",
    )
    quantity: Optional[int] = Field(None, ge=0, description="Updated total quantity.")
    available_quantity: Optional[int] = Field(
        None, ge=0, description="Updated available quantity."
    )
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[ResourceStatus] = Field(None, description="Updated operational status.")
    assigned_disaster: Optional[UUID] = Field(
        None, description="UUID of the disaster to assign/reassign this resource to."
    )


class ResourceResponse(FullResponseSchema, ResourceBase):
    """
    ORM-compatible response schema for Resource.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    Inherits all inventory fields from ResourceBase.
    """

    assigned_disaster: Optional[UUID] = Field(
        None,
        description=(
            "UUID of the disaster this resource is currently assigned to. "
            "Null when the resource is unallocated."
        ),
    )


class AllocateRequest(BaseSchema):
    """Request body for PATCH /resources/{id}/allocate (Government + NGO)."""

    disaster_id: UUID = Field(
        ...,
        description="UUID of the disaster event to allocate this resource to.",
    )
    quantity_to_allocate: int = Field(
        ...,
        ge=1,
        description="Number of units to allocate. Must be ≥ 1 and ≤ available_quantity.",
    )


class ReleaseRequest(BaseSchema):
    """Request body for PATCH /resources/{id}/release (Government only)."""

    quantity_to_release: int = Field(
        ...,
        ge=1,
        description=(
            "Number of units to release back into available stock. "
            "Must be ≥ 1 and ≤ currently allocated quantity."
        ),
    )
