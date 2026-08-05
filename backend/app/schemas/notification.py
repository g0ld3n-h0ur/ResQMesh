"""
app/schemas/notification.py

Pydantic v2 schemas for the Notification model.

Schema hierarchy
----------------
NotificationBase     — shared readable fields
  └── NotificationCreate  — input for POST /notifications
  └── NotificationUpdate  — input for PATCH /notifications/{id}
NotificationResponse — ORM-compatible full response

Delivery modes
--------------
1. Broadcast:       recipient_role set, recipient_id null
2. User-specific:   recipient_id set, recipient_role optional for context
3. Both:            targeting a user and preserving role context for audit

At least one of recipient_role or recipient_id must be provided in Create.
This is enforced via a model_validator to provide a meaningful API error.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import NotificationPriority, RoleEnum
from app.schemas.base import BaseSchema, FullResponseSchema


class NotificationBase(BaseSchema):
    """Shared readable fields for Notification."""

    title: str = Field(..., min_length=1, max_length=255, description="Notification subject line.")
    message: str = Field(..., min_length=1, description="Full notification body text.")
    priority: NotificationPriority = Field(
        NotificationPriority.MEDIUM, description="Urgency level."
    )
    recipient_role: Optional[RoleEnum] = Field(
        None, description="Target role for broadcast delivery (null for user-specific)."
    )
    recipient_id: Optional[UUID] = Field(
        None, description="Target user UUID for user-specific delivery (null for broadcast)."
    )
    is_read: bool = Field(False, description="True when the recipient has acknowledged.")


class NotificationCreate(BaseSchema):
    """Input schema for creating a new notification."""

    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM)
    recipient_role: Optional[RoleEnum] = None
    recipient_id: Optional[UUID] = None

    @model_validator(mode="after")
    def must_have_recipient(self) -> "NotificationCreate":
        """Require at least one delivery target."""
        if self.recipient_role is None and self.recipient_id is None:
            raise ValueError(
                "At least one of recipient_role or recipient_id must be provided."
            )
        return self


class NotificationUpdate(BaseSchema):
    """Partial update schema — typically used only to mark as read."""

    is_read: Optional[bool] = Field(None, description="Set to true to mark as read.")
    priority: Optional[NotificationPriority] = None


class NotificationResponse(FullResponseSchema, NotificationBase):
    """
    ORM-compatible response schema for Notification.

    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    pass
