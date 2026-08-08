"""
app/schemas/user.py

Pydantic v2 schemas for the User model.

Schema hierarchy
----------------
UserBase        — shared readable fields (no sensitive data)
  └── UserCreate    — input schema for POST /users (includes password)
  └── UserUpdate    — input schema for PATCH /users/{id} (all fields optional)
UserResponse    — ORM-compatible response schema (no password_hash)

Notes
-----
- password_hash is NEVER included in any response schema.
- UserCreate accepts a plain-text 'password' field; the service layer
  is responsible for hashing before persisting.
- Email is validated for basic format only (no email-validator dependency).
  Add 'email-validator' to requirements and switch to EmailStr for stricter checks.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import RoleEnum
from app.schemas.base import BaseSchema, FullResponseSchema


class UserBase(BaseSchema):
    """Shared readable fields for User — safe to expose in responses."""

    full_name: str = Field(..., min_length=1, max_length=255, description="Full display name.")
    email: str = Field(..., max_length=255, description="Unique email address for login.")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number.")
    role: RoleEnum = Field(..., description="Operational role on the platform.")
    organization_name: Optional[str] = Field(
        None, max_length=255, description="Government body, NGO, or hospital name."
    )
    district: Optional[str] = Field(None, max_length=100, description="Administrative district.")
    state: Optional[str] = Field(None, max_length=100, description="State or province.")
    country: Optional[str] = Field("India", max_length=100, description="Country of location.")
    is_active: bool = Field(True, description="False when the account is deactivated.")

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: str) -> str:
        """Basic email format check."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address format.")
        return v.lower().strip()


class UserCreate(UserBase):
    """Input schema for creating a new user account."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plain-text password. Service layer hashes before storage.",
    )


class UserUpdate(BaseSchema):
    """Partial update schema for PATCH operations — all fields optional."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    organization_name: Optional[str] = Field(None, max_length=255)
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(FullResponseSchema, UserBase):
    """
    ORM-compatible response schema for User.

    password_hash is deliberately excluded.
    Inherits id, created_at, updated_at, is_deleted from FullResponseSchema.
    """

    pass


class UserPublicResponse(BaseSchema):
    """
    Minimal public-safe User representation for embedding in other responses.

    Contains only non-sensitive identity fields.
    """

    id: UUID
    full_name: str
    role: RoleEnum
    district: Optional[str] = None
    organization_name: Optional[str] = None
