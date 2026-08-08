"""
app/schemas/auth.py

Authentication-specific Pydantic v2 schemas.

TokenResponse          — JWT pair returned by /login and /refresh.
UserRegisterBase       — Shared fields for every registration endpoint.
Register*Request       — Role-specific registration schemas with field rules.
LoginRequest           — JSON-body login alternative (API clients).
RefreshRequest         — Refresh token body.

Validation applied at the schema layer:
  - Email format and normalisation (lowercase, strip)
  - Phone number digit count (7–15 digits)
  - Password minimum length (8 chars; strength checked in service layer)
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# Token schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseSchema):
    """JWT token pair returned after a successful login or token refresh."""

    access_token: str = Field(
        ...,
        description="Short-lived Bearer access token for API requests.",
    )
    refresh_token: str = Field(
        ...,
        description="Long-lived token used to obtain a new access token.",
    )
    token_type: str = Field(
        "bearer",
        description="Always 'bearer' per OAuth2 specification.",
    )
    expires_in: int = Field(
        ...,
        description="Access token lifetime in seconds.",
    )


# ---------------------------------------------------------------------------
# Shared registration base
# ---------------------------------------------------------------------------

class UserRegisterBase(BaseSchema):
    """
    Shared registration fields for all five role-specific endpoints.

    Role is determined by the endpoint path, not by this schema.
    """

    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full display name of the registering user.",
    )
    email: str = Field(
        ...,
        max_length=255,
        description="Unique email address — used for login and notifications.",
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Contact phone number (optional, 7–15 digits).",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description=(
            "Account password. Minimum 8 characters. "
            "Must include uppercase, lowercase, digit, and special character."
        ),
    )
    organization_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Government body, NGO, or hospital name.",
    )
    district: Optional[str] = Field(
        None,
        max_length=100,
        description="Administrative district for geographic filtering.",
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State or province.",
    )
    country: str = Field(
        "India",
        max_length=100,
        description="Country. Defaults to India.",
    )

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        """Lowercase, strip, and basic format validation."""
        v = v.lower().strip()
        parts = v.split("@")
        if len(parts) != 2 or not parts[0] or "." not in parts[1]:
            raise ValueError(
                "Invalid email address. Expected format: user@domain.tld"
            )
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Ensure phone contains 7–15 digits (ignoring separators)."""
        if v is None:
            return v
        digit_count = sum(1 for c in v if c.isdigit())
        if not (7 <= digit_count <= 15):
            raise ValueError(
                "Phone number must contain 7–15 digits. "
                "Include the country code (e.g. +91)."
            )
        return v.strip()


# ---------------------------------------------------------------------------
# Role-specific registration schemas
# ---------------------------------------------------------------------------

class RegisterGovernmentRequest(UserRegisterBase):
    """
    Registration form for Government authority accounts.

    organization_name is required — every government user must belong to
    a registered authority (e.g. 'Tamil Nadu Disaster Management Authority').
    """

    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the government authority or ministry.",
    )


class RegisterNGORequest(UserRegisterBase):
    """
    Registration form for NGO staff accounts.

    organization_name is required — NGO users must specify their organisation.
    """

    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Official name of the Non-Governmental Organisation.",
    )


class RegisterVolunteerRequest(UserRegisterBase):
    """
    Registration form for Volunteer accounts.

    All fields except full_name, email, and password are optional.
    """

    pass


class RegisterHospitalRequest(UserRegisterBase):
    """
    Registration form for Hospital staff accounts.

    organization_name is required — hospital users must specify their facility.
    """

    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Official name of the hospital or medical institution.",
    )


class RegisterCitizenRequest(UserRegisterBase):
    """
    Registration form for Citizen accounts.

    All fields except full_name, email, and password are optional.
    Citizens may also submit emergency reports without an account.
    """

    pass


# ---------------------------------------------------------------------------
# Login schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseSchema):
    """
    JSON-body login schema for non-Swagger API clients.

    The primary /login endpoint uses OAuth2PasswordRequestForm (form data)
    for Swagger Authorize compatibility. This schema is provided for
    documentation and alternative client integrations.
    """

    email: str = Field(..., description="Registered email address.")
    password: str = Field(..., description="Account password.")


class RefreshRequest(BaseSchema):
    """Body schema for the token refresh endpoint."""

    refresh_token: str = Field(
        ...,
        description="Valid refresh token obtained from /login.",
    )
