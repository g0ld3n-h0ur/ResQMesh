"""
app/api/v1/auth.py

Authentication router — framework skeleton.

Endpoints defined here handle user registration, login, token refresh,
and logout flows. JWT and password logic will be wired from
app.core.security in the authentication implementation phase.

Prefix  : /api/v1/auth
Tags    : Authentication
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_AUTH

router = APIRouter(
    prefix="/auth",
    tags=[API_V1_TAG_AUTH],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to Phase 2
# ---------------------------------------------------------------------------
# POST /auth/register   → Register a new user
# POST /auth/login      → Obtain JWT access + refresh tokens
# POST /auth/refresh    → Refresh an expired access token
# POST /auth/logout     → Revoke / invalidate a refresh token
# GET  /auth/me         → Return the currently authenticated user profile
