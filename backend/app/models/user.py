"""
app/models/user.py

User model — platform accounts covering all five operational roles.

Indexes
-------
- email       (unique)
- role        (filter by role for dashboards)
- district    (geographic lookups)
- role+district (composite — common dashboard query pattern)
- role+is_active (composite — active users per role)

Relationships
-------------
- emergency_reports  → EmergencyReport  (one-to-many, via reported_by_user_id)
- assignments        → Assignment       (volunteer assignments, via volunteer_id)
- ngo_assignments    → Assignment       (NGO assignments, via ngo_id)
- notifications      → Notification     (one-to-many, via recipient_id)
- reported_disasters → Disaster         (one-to-many, via reported_by)

Loading strategy: lazy="select" throughout.
Service layer must use selectinload() / joinedload() options to avoid N+1.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum as SAEnum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import RoleEnum

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.disaster import Disaster
    from app.models.emergency_report import EmergencyReport
    from app.models.notification import Notification


class User(BaseModel):
    """Registered platform user — covers all five operational roles."""

    __tablename__ = "users"

    # ---------------------------------------------------------------------- #
    # Columns                                                                 #
    # ---------------------------------------------------------------------- #
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Full display name of the user.",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address used for login and notifications.",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Contact phone number (E.164 format recommended).",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="bcrypt password hash. Never expose in API responses.",
    )
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role_enum", create_constraint=True, native_enum=False),
        nullable=False,
        index=True,
        doc="Operational role determining dashboard access and permissions.",
    )
    organization_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Name of the government body, NGO, or hospital the user belongs to.",
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Administrative district — used for geographic filtering.",
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="State or province of the user's location.",
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="India",
        doc="Country of the user's location. Defaults to India.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="False when the account has been deactivated.",
    )

    # ---------------------------------------------------------------------- #
    # Relationships                                                            #
    # ---------------------------------------------------------------------- #
    emergency_reports: Mapped[list["EmergencyReport"]] = relationship(
        "EmergencyReport",
        back_populates="reported_by_user",
        cascade="save-update, merge",
        lazy="select",
        doc="Field reports submitted by this user.",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        primaryjoin="User.id == Assignment.volunteer_id",
        back_populates="volunteer",
        cascade="save-update, merge",
        lazy="select",
        doc="Disaster assignments where this user acts as a volunteer.",
    )
    ngo_assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        primaryjoin="User.id == Assignment.ngo_id",
        back_populates="ngo",
        cascade="save-update, merge",
        lazy="select",
        doc="Disaster assignments where this user represents an NGO.",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="recipient",
        cascade="save-update, merge",
        lazy="select",
        doc="Notifications addressed to this specific user.",
    )
    reported_disasters: Mapped[list["Disaster"]] = relationship(
        "Disaster",
        back_populates="reporter",
        cascade="save-update, merge",
        lazy="select",
        doc="Disaster events originally reported by this user.",
    )

    # ---------------------------------------------------------------------- #
    # Composite indexes                                                       #
    # ---------------------------------------------------------------------- #
    __table_args__ = (
        Index("ix_users_role_district", "role", "district"),
        Index("ix_users_role_is_active", "role", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
