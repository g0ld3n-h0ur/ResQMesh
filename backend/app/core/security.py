"""
app/core/security.py

Production-ready JWT and password security utilities.

Responsibilities
----------------
- Password hashing (bcrypt via passlib)
- Password strength enforcement
- JWT access token creation (HS256, includes role in payload)
- JWT refresh token creation
- JWT decoding and verification
- OAuth2PasswordBearer scheme for FastAPI Swagger integration

All configuration values (SECRET_KEY, ALGORITHM, token expiry) are
read from Settings, which loads them from the .env file at startup.

Token payload structure (access)
---------------------------------
{
    "sub":  "<user_uuid_string>",   # Subject — user primary key
    "role": "<role_value>",          # Embedded for fast RBAC without DB lookup
    "type": "access",
    "iat":  <issued_at_unix_ts>,
    "exp":  <expiry_unix_ts>,
}

Token payload structure (refresh)
-----------------------------------
{
    "sub":  "<user_uuid_string>",
    "type": "refresh",
    "iat":  <issued_at_unix_ts>,
    "exp":  <expiry_unix_ts>,
}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # noqa: F401  (JWTError re-exported for callers)
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing context
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# OAuth2 bearer scheme
# Declaring this here (not in dependencies) ensures FastAPI registers the
# Swagger "Authorize" button automatically when oauth2_scheme is used
# anywhere in the dependency graph.
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    scheme_name="JWT",
    description=(
        "Enter the **Bearer** token obtained from POST /api/v1/auth/login. "
        "Format: `Bearer <token>`"
    ),
)


# ---------------------------------------------------------------------------
# Token payload dataclass
# ---------------------------------------------------------------------------
@dataclass
class TokenPayload:
    """
    Typed representation of a decoded JWT payload.

    Attributes:
        sub:        User UUID string (primary key).
        role:       User role value string (e.g. 'government').
        token_type: 'access' or 'refresh'.
        exp:        Expiration as Unix timestamp float.
    """

    sub: str
    role: str
    token_type: str
    exp: float


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain_password:  The password provided by the user at login.
        hashed_password: The bcrypt hash retrieved from the database.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password with bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        A bcrypt-hashed password string safe for database storage.
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> None:
    """
    Enforce production-grade password complexity rules.

    Requirements:
        - Minimum 8 characters
        - At least one uppercase letter (A–Z)
        - At least one lowercase letter (a–z)
        - At least one digit (0–9)
        - At least one special character (!@#$%^&* etc.)

    Args:
        password: The plain-text password to evaluate.

    Raises:
        ValueError: With a human-readable message describing the violation.
                    Caller is responsible for converting to an HTTPException.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must contain at least one uppercase letter (A–Z)."
        )

    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must contain at least one lowercase letter (a–z)."
        )

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit (0–9).")

    if not re.search(r"[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/~`\"'\\]", password):
        raise ValueError(
            "Password must contain at least one special character "
            "(!@#$%^&*()-_=+[]{}|;:,.<>?/~`)."
        )


# ---------------------------------------------------------------------------
# JWT utilities
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | Any,
    role: str = "",
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    The `role` is embedded in the payload so that RBAC checks can run without
    a database round-trip on every request (fast path for permission guards).

    Args:
        subject:      Token subject — the user's UUID as a string.
        role:         User's role value string (e.g. 'government').
        expires_delta: Override the default expiry duration.

    Returns:
        Encoded JWT string signed with HS256.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT refresh token.

    Refresh tokens carry only the subject and type — no role. They are
    used exclusively to obtain new access tokens, not to access resources.

    Args:
        subject:      Token subject — the user's UUID as a string.
        expires_delta: Override the default expiry duration.

    Returns:
        Encoded JWT string signed with HS256.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Verifies signature, expiry, and algorithm. Does NOT enforce token type —
    callers are responsible for checking payload['type'].

    Args:
        token: Encoded JWT string (without 'Bearer ' prefix).

    Returns:
        Decoded payload dictionary.

    Raises:
        jose.JWTError: If the token is invalid, expired, or tampered.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
