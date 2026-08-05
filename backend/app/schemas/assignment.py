"""
app/schemas/assignment.py

Pydantic v2 schemas for the Assignment model.

Schema hierarchy
----------------
AssignmentBase     — shared readable fields
  └── AssignmentCreate  — input for POST /assignments
  └── AssignmentUpdate  — input for PATCH /assignments/{id}
AssignmentResponse — ORM-compatible full response

Notes
-----
- Only disaster_id is required in Create.
- All other FK fields (resource_id, volunteer_id, ngo_id, hospital_id) are optional,
  enabling flexible partial assignments.
- At least one of resource_id, volunteer_id, ngo_id, or hospital_id should be
  provided for a meaningful assignment, but this is enforced at the service layer
  to keep the schema flexible for evolving business rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.enums import AssignmentStatus
from app.schemas.base import BaseSchema, FullResponseSchema


class AssignmentBase(BaseSchema):
    """Shared readable fields for Assignment."""

    resource_id: Optional[UUID] = Field(
        None, description="UUID of the assigned resource (null if not resource-based)."
    )
    volunteer_id: Optional[UUID] = Field(
        None, description="UUID of the assigned volunteer user (null if not volunteer-based)."
    )
    ngo_id: Optional[UUID] = Field(
        None, description="UUID of the assigned NGO user (null if not NGO-based)."
    )
    hospital_id: Optional[UUID] = Field(
        None, description="UUID of the assigned hospital (null if not hospital-based)."
    )
    status: AssignmentStatus = Field(
        AssignmentStatus.PENDING, description="Current assignment lifecycle status."
    )


class AssignmentCreate(AssignmentBase):
    """Input schema for creating a new assignment."""

    disaster_id: UUID = Field(
        ..., description="UUID of the disaster this assignment belongs to. Required."
    )


class AssignmentUpdate(BaseSchema):
    """Partial update schema for PATCH operations."""

    resource_id: Optional[UUID] = None
    volunteer_id: Optional[UUID] = None
    ngo_id: Optional[UUID] = None
    hospital_id: Optional[UUID] = None
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(FullResponseSchema, AssignmentBase):
    """
    ORM-compatible response schema for Assignment.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    disaster_id: UUID = Field(..., description="UUID of the associated disaster.")
    assigned_at: datetime = Field(..., description="Timestamp when the assignment was created.")
