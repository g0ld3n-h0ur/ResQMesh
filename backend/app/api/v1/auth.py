"""
app/api/v1/auth.py

Authentication router — complete implementation.

Prefix : /api/v1/auth
Tags   : Authentication

Endpoints
---------
POST  /auth/register/government  — Register a government authority account
POST  /auth/register/ngo         — Register an NGO staff account
POST  /auth/register/volunteer   — Register a volunteer account
POST  /auth/register/hospital    — Register a hospital staff account
POST  /auth/register/citizen     — Register a citizen account
POST  /auth/login                — Obtain JWT access + refresh tokens (OAuth2 form)
GET   /auth/me                   — Return the authenticated user's profile
POST  /auth/refresh              — Exchange a refresh token for a new access token
POST  /auth/logout               — Stateless logout (client discards token)

Access control
--------------
Public (no auth required):
  /register/*  — All registration endpoints
  /login       — Token issuance
Protected:
  /me          — Any authenticated active user
  /refresh     — Any authenticated active user (refresh token in body)
  /logout      — Any authenticated active user

Swagger integration
-------------------
The oauth2_scheme declared in app.core.security uses OAuth2PasswordBearer,
which causes FastAPI to render an "Authorize" button in Swagger UI.
The /login endpoint accepts application/x-www-form-urlencoded (OAuth2 form)
so the Swagger Authorize dialog works out of the box.

Response envelope
-----------------
All responses (success and error) use the standardised envelope from
app.utils.response:
  {
      "success": true | false,
      "message": "...",
      "data": { ... } | null,
      "errors": null | [ ... ]
  }

Exception: /login returns the raw token dict at the top level to satisfy
the OAuth2 specification (Swagger reads 'access_token' and 'token_type'
from the top-level response to populate the Authorize dialog).
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.dependencies.auth import CurrentUser, get_current_active_user
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.auth import (
    RefreshRequest,
    RegisterCitizenRequest,
    RegisterGovernmentRequest,
    RegisterHospitalRequest,
    RegisterNGORequest,
    RegisterVolunteerRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import authenticate_user, create_token_pair, register_user
from app.utils.constants import API_V1_TAG_AUTH
from app.utils.response import success_response

router = APIRouter(
    prefix="/auth",
    tags=[API_V1_TAG_AUTH],
)


# ---------------------------------------------------------------------------
# Private helper — serialize User ORM instance to safe JSON-compatible dict
# ---------------------------------------------------------------------------
def _user_to_dict(user: User) -> dict[str, Any]:
    """
    Convert a User ORM instance to a JSON-serialisable dict.

    Uses UserResponse (which excludes password_hash) with mode='json' so
    UUID and datetime fields are rendered as strings.
    """
    return UserResponse.model_validate(user).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Registration endpoints — public, no auth required
# ---------------------------------------------------------------------------

@router.post(
    "/register/government",
    status_code=status.HTTP_201_CREATED,
    summary="Register a Government Authority account",
    response_description="The newly created government user profile.",
)
async def register_government(
    data: RegisterGovernmentRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Register a new **Government** authority user account.

    - `organization_name` is **required** — specify the authority or ministry.
    - The assigned role is `government` (determined by this endpoint).
    - Passwords must be ≥8 chars with uppercase, lowercase, digit, and special character.
    - Duplicate email and duplicate phone are rejected with HTTP 400.
    """
    user = register_user(db, data, RoleEnum.GOVERNMENT)
    return success_response(
        data=_user_to_dict(user),
        message="Government account registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/register/ngo",
    status_code=status.HTTP_201_CREATED,
    summary="Register an NGO Staff account",
    response_description="The newly created NGO user profile.",
)
async def register_ngo(
    data: RegisterNGORequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Register a new **NGO** staff user account.

    - `organization_name` is **required** — specify the NGO name.
    - The assigned role is `ngo`.
    - NGO users can manage resources and assign volunteers.
    """
    user = register_user(db, data, RoleEnum.NGO)
    return success_response(
        data=_user_to_dict(user),
        message="NGO account registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/register/volunteer",
    status_code=status.HTTP_201_CREATED,
    summary="Register a Volunteer account",
    response_description="The newly created volunteer user profile.",
)
async def register_volunteer(
    data: RegisterVolunteerRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Register a new **Volunteer** account.

    - `organization_name` is optional.
    - The assigned role is `volunteer`.
    - Volunteers can view and update their assigned tasks.
    """
    user = register_user(db, data, RoleEnum.VOLUNTEER)
    return success_response(
        data=_user_to_dict(user),
        message="Volunteer account registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/register/hospital",
    status_code=status.HTTP_201_CREATED,
    summary="Register a Hospital Staff account",
    response_description="The newly created hospital user profile.",
)
async def register_hospital(
    data: RegisterHospitalRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Register a new **Hospital** staff account.

    - `organization_name` is **required** — specify the hospital name.
    - The assigned role is `hospital`.
    - Hospital users can update bed, ambulance, and oxygen availability.
    """
    user = register_user(db, data, RoleEnum.HOSPITAL)
    return success_response(
        data=_user_to_dict(user),
        message="Hospital account registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/register/citizen",
    status_code=status.HTTP_201_CREATED,
    summary="Register a Citizen account",
    response_description="The newly created citizen user profile.",
)
async def register_citizen(
    data: RegisterCitizenRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Register a new **Citizen** account.

    - All fields except `full_name`, `email`, and `password` are optional.
    - The assigned role is `citizen`.
    - Citizens may also submit emergency reports **without** an account.
    """
    user = register_user(db, data, RoleEnum.CITIZEN)
    return success_response(
        data=_user_to_dict(user),
        message="Citizen account registered successfully.",
        status_code=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Login — public, returns OAuth2-compatible response
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    summary="Obtain JWT access and refresh tokens",
    response_description=(
        "JWT access token, refresh token, token type, and expiry (seconds)."
    ),
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """
    Authenticate with email and password to receive JWT tokens.

    **Swagger Authorize dialog**: Enter your email in the `username` field
    and your password in the `password` field, then click **Authorize**.
    After logging in, all protected endpoints will automatically include
    your Bearer token.

    Returns the standard OAuth2 token structure so the Swagger Authorize
    dialog correctly extracts `access_token` and `token_type`.

    - `username` field — enter your registered **email address**
    - `password` field — enter your account password
    """
    # form_data.username contains the email (OAuth2 spec uses 'username')
    user = authenticate_user(db, form_data.username, form_data.password)
    tokens = create_token_pair(user)

    # Return raw token dict (not success_response wrapper) so Swagger
    # Authorize dialog can extract access_token from the top level
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
    }


# ---------------------------------------------------------------------------
# Token refresh — protected (requires valid refresh token in body)
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    summary="Refresh an expired access token",
    response_description="A new JWT access token.",
)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Exchange a valid refresh token for a new access token.

    - The refresh token must be the one issued at login (not an access token).
    - Returns a new access + refresh token pair.
    - The old refresh token should be discarded by the client.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type. Provide a refresh token, not an access token.",
        )

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception

    stmt = (
        select(User)
        .where(User.id == user_uuid)
        .where(User.is_deleted.is_(False))
        .where(User.is_active.is_(True))
    )
    user: User | None = db.execute(stmt).scalar_one_or_none()

    if user is None:
        raise credentials_exception

    tokens = create_token_pair(user)
    return success_response(
        data=tokens.model_dump(),
        message="Access token refreshed successfully.",
    )


# ---------------------------------------------------------------------------
# Current user profile — protected
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    summary="Retrieve the authenticated user's profile",
    response_description="Full user profile (no password hash).",
)
async def get_me(
    current_user: CurrentUser,
) -> Any:
    """
    Return the profile of the currently authenticated user.

    Requires a valid Bearer access token in the Authorization header.
    The password hash is **never** included in the response.
    """
    return success_response(
        data=_user_to_dict(current_user),
        message="User profile retrieved successfully.",
    )


# ---------------------------------------------------------------------------
# Logout — protected, stateless
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    summary="Logout (stateless — invalidate token client-side)",
    response_description="Confirmation that logout was processed.",
)
async def logout(
    current_user: CurrentUser,
) -> Any:
    """
    Log out the current user.

    **Stateless JWT note**: JWTs cannot be invalidated server-side without
    a token blacklist (e.g., Redis). The client must delete the stored tokens
    on receipt of this response.

    Future enhancement: token blacklisting with Redis TTL matching
    the access token expiry will be implemented in Phase 5.
    """
    return success_response(
        message=(
            f"Goodbye, {current_user.full_name}. "
            "Logged out successfully. Please discard your access and refresh tokens."
        ),
    )
