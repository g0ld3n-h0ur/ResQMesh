"""
app/services/auth_service.py

Authentication business logic service.

This module implements the core authentication operations:
  - User lookup by email or phone
  - New user registration (with duplicate checks and password hashing)
  - Credential verification (login)
  - JWT token pair generation

Design principles
-----------------
- All database queries use SQLAlchemy 2.0 select() API.
- Passwords are NEVER stored or logged in plain text.
- Duplicate email and duplicate phone checks are enforced before insert.
- Password strength is validated here (service layer) after Pydantic's
  basic min_length check passes at the schema boundary.
- HTTP exceptions (400, 401, 403) are raised directly so FastAPI's
  exception handler propagates them correctly to the client.

Circular import prevention
---------------------------
  This module imports ONLY from:
    - app.core.security         (no service imports)
    - app.core.config           (settings only)
    - app.database.session      (no auth imports)
    - app.models.user / enums   (no auth imports)
    - app.schemas.auth          (no service imports)
  No imports from app.dependencies or app.core.permissions.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegisterBase


# ---------------------------------------------------------------------------
# User lookup helpers
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a non-deleted user by (normalised) email address.

    Args:
        db:    Active database session.
        email: Email to look up (should be lowercased by caller or schema).

    Returns:
        User instance if found and not soft-deleted, else None.
    """
    stmt = (
        select(User)
        .where(User.email == email.lower().strip())
        .where(User.is_deleted.is_(False))
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """
    Retrieve a non-deleted user by phone number.

    Args:
        db:    Active database session.
        phone: Phone number string (e.g. '+919876543210').

    Returns:
        User instance if found and not soft-deleted, else None.
    """
    stmt = (
        select(User)
        .where(User.phone == phone.strip())
        .where(User.is_deleted.is_(False))
    )
    return db.execute(stmt).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(
    db: Session,
    data: UserRegisterBase,
    role: RoleEnum,
) -> User:
    """
    Register a new platform user.

    Validation sequence (fail-fast, ordered by expense):
      1. Password strength check (CPU-cheap, no DB).
      2. Duplicate email check (single indexed SELECT).
      3. Duplicate phone check (single indexed SELECT, only if phone provided).
      4. Bcrypt hash + INSERT.

    Args:
        db:   Active database session.
        data: Validated registration payload from the request schema.
        role: User role — determined by the route endpoint, not the payload.

    Returns:
        The newly created and persisted User ORM instance.

    Raises:
        HTTPException 400: Weak password, duplicate email, or duplicate phone.
        HTTPException 500: Unexpected database error.
    """
    # 1. Password strength (raises ValueError on failure)
    try:
        validate_password_strength(data.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # 2. Duplicate email
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "An account with this email address already exists. "
                "Please use a different email or log in."
            ),
        )

    # 3. Duplicate phone (only when a phone number is provided)
    if data.phone and get_user_by_phone(db, data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This phone number is already registered to another account. "
                "Please use a different phone number."
            ),
        )

    # 4. Create user
    user = User(
        full_name=data.full_name,
        email=data.email.lower().strip(),
        phone=data.phone.strip() if data.phone else None,
        password_hash=hash_password(data.password),
        role=role,
        organization_name=getattr(data, "organization_name", None),
        district=data.district,
        state=data.state,
        country=data.country or "India",
        is_active=True,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again.",
        ) from exc

    return user


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    """
    Verify credentials and return the authenticated User.

    Deliberately uses a generic error message for both 'user not found' and
    'wrong password' to prevent user enumeration attacks.

    Args:
        db:       Active database session.
        email:    Login email address.
        password: Plain-text password provided by the user.

    Returns:
        The authenticated User ORM instance.

    Raises:
        HTTPException 401: Invalid credentials (user not found or wrong password).
        HTTPException 403: Valid credentials but account is deactivated.
    """
    _INVALID_CREDS = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Invalid email address or password. "
            "Please check your credentials and try again."
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = get_user_by_email(db, email)

    # Use constant-time comparison via passlib even when user not found,
    # to prevent timing attacks from revealing valid email addresses.
    if user is None:
        # Perform a dummy verification to maintain constant response time
        verify_password("dummy_password_123", hash_password("dummy_password_123"))
        raise _INVALID_CREDS

    if not verify_password(password, user.password_hash):
        raise _INVALID_CREDS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account has been deactivated. "
                "Please contact an administrator for assistance."
            ),
        )

    return user


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------

def create_token_pair(user: User) -> TokenResponse:
    """
    Generate a JWT access + refresh token pair for a user.

    The user's role is embedded in the access token payload so that
    RBAC permission guards can run without an additional DB query.

    Args:
        user: Authenticated and active User ORM instance.

    Returns:
        TokenResponse containing access_token, refresh_token,
        token_type='bearer', and expires_in (seconds).
    """
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
