"""
app/models/notification.py

Notification model — alert and broadcast system for the platform.

Supports two delivery modes:
  1. Role-based broadcast: recipient_role is set, recipient_id is null.
     Delivered to all active users with the specified role.
  2. User-specific: recipient_id is set (FK → users.id).
     Delivered to one specific user regardless of role.
  3. Both: When both are set, the record targets a specific user
     but the role context is preserved for audit/filtering.

Indexes
-------
- recipient_id      (user inbox queries)
- recipient_role    (role-based broadcast queries)
- priority          (filter by urgency)
- is_read           (unread count queries)
- recipient_id+is_read (composite — unread inbox per user)
- recipient_role+priority (composite — role-based alert filtering)

Relationships
-------------
- recipient → User (many-to-one, nullable — null for broadcast notifications)

Loading strategy: lazy="select"
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import NotificationPriority, RoleEnum

if TYPE_CHECKING:
    from app.models.user import User


class Notification(BaseModel):
    """A platform alert notification — delivered to a user or a role group."""

    __tablename__ = "notifications"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Short subject line of the notification.",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full notification body text.",
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        SAEnum(
            NotificationPriority,
            name="notification_priority",
            create_constraint=True,
            native_enum=False,
        ),
        nullable=False,
        default=NotificationPriority.MEDIUM,
        index=True,
        doc="Urgency level of this notification.",
    )
    # Role-based broadcast target (null for user-specific notifications)
    recipient_role: Mapped[Optional[RoleEnum]] = mapped_column(
        SAEnum(
            RoleEnum,
            name="role_enum_notif",
            create_constraint=False,  # role_enum already constrained on users table
            native_enum=False,
        ),
        nullable=True,
        index=True,
        doc="Target role for broadcast notifications. Null for user-specific delivery.",
    )
    # User-specific target (null for broadcast notifications)
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="UUID of the specific recipient user. Null for role-based broadcasts.",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="True when the recipient has acknowledged the notification.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    recipient: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="notifications",
        lazy="select",
        doc="The specific user recipient (null for broadcast notifications).",
    )

    # ---------------------------------------------------------------------- #
    # Composite indexes                                                       #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        Index("ix_notifications_recipient_is_read", "recipient_id", "is_read"),
        Index("ix_notifications_role_priority", "recipient_role", "priority"),
        Index("ix_notifications_priority_is_read", "priority", "is_read"),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} title={self.title!r} "
            f"priority={self.priority} is_read={self.is_read}>"
        )
