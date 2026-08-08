"""
app/dependencies/auth.py

Core FastAPI authentication dependencies.

These callables are injected via Depends() into any protected route.
They decode the Bearer token, resolve the User record from the database,
and enforce active-account and type-safety guards.

Dependency resolution chain
----------------------------
  oauth2_scheme (Bearer extractor)
      │
      ▼
  get_current_user()          ← decodes JWT, loads User from DB
      │
      ▼
  get_current_active_user()   ← asserts is_active == True
      │
      ▼
  get_current_role()          ← returns user.role

Type aliases
------------
  CurrentUser  — Annotated[User, Depends(get_current_active_user)]
                 Use in route signatures for clean, readable code.

Circular import prevention
---------------------------
  This module imports ONLY from:
    - app.core.security     (no app-level imports)
    - app.database.session  (no auth imports)
    - app.models.user       (no auth imports)
    - app.models.enums      (no auth imports)
  No imports from app.core.permissions or app.services.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token, oauth2_scheme
from app.database.session import get_db
from app.models.enums import RoleEnum
from app.models.user import User

# ---------------------------------------------------------------------------
# Shared credentials exception — used in multiple places
# ---------------------------------------------------------------------------
_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


# ---------------------------------------------------------------------------
# Core dependency functions
# ---------------------------------------------------------------------------

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Resolve the authenticated User from a Bearer token.

    Steps:
      1. Decode and verify the JWT signature and expiry.
      2. Assert the token type is 'access' (not 'refresh').
      3. Extract the user UUID from the 'sub' claim.
      4. Load the User record from the database.
      5. Reject if the record is soft-deleted.

    Raises:
        HTTPException 401: If the token is invalid, expired, or the user
                           cannot be found.
    """
    try:
        payload = decode_token(token)
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    # Enforce token type — prevent refresh tokens being used as access tokens
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use an access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract and validate subject (user UUID)
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise _CREDENTIALS_EXCEPTION

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise _CREDENTIALS_EXCEPTION

    # Load User from database (SQLAlchemy 2.0 select API)
    stmt = (
        select(User)
        .where(User.id == user_uuid)
        .where(User.is_deleted.is_(False))
    )
    user: User | None = db.execute(stmt).scalar_one_or_none()

    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Assert the resolved user's account is active.

    A user may be valid (in the database, not deleted) but deactivated
    by an administrator. This dependency rejects deactivated accounts
    with a 403 Forbidden — not 401, because the token itself is valid.

    Raises:
        HTTPException 403: If the user's account is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account is deactivated. "
                "Please contact an administrator to restore access."
            ),
        )
    return current_user


def get_current_role(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RoleEnum:
    """
    Return the role of the currently authenticated active user.

    Use this dependency when you need the role value directly rather
    than the full User object.

    Returns:
        The user's RoleEnum member.
    """
    return current_user.role


# ---------------------------------------------------------------------------
# Type aliases for clean route signatures
# ---------------------------------------------------------------------------

CurrentUser = Annotated[User, Depends(get_current_active_user)]
"""
Annotated type alias for the current active user.

Usage in route handlers::

    @router.get("/protected")
    async def protected_route(user: CurrentUser) -> ...:
        ...
"""
