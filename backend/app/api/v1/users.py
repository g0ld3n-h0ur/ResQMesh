"""
app/api/v1/users.py

Minimal user directory router — lets coordination-level roles look up
active users by role (e.g. "which volunteers/NGOs can I assign to this
disaster"). Only exposes public-safe identity fields (id, full_name, role);
never password_hash or contact info.

Prefix : /api/v1/users
Tags   : Users
"""

from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import RequireAdminRoles
from app.database.session import get_db
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.user import UserPublicResponse
from app.utils.constants import API_V1_TAG_USERS
from app.utils.response import success_response

router = APIRouter(
    prefix="/users",
    tags=[API_V1_TAG_USERS],
)


@router.get(
    "/",
    summary="List active users, optionally filtered by role",
    description="""
Retrieve a minimal, public-safe list of active users (id, full_name, role
only — no contact info or credentials). Primarily used to populate
assignee pickers when creating an Assignment (e.g. "list all volunteers").

Requires: **Government** or **NGO** role.
    """,
)
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: RequireAdminRoles,
    role: Optional[RoleEnum] = Query(None, description="Filter by role."),
) -> Any:
    stmt = select(User).where(User.is_deleted.is_(False), User.is_active.is_(True))
    if role:
        stmt = stmt.where(User.role == role)
    stmt = stmt.order_by(User.full_name.asc())

    users = list(db.execute(stmt).scalars().all())
    return success_response(
        data=[UserPublicResponse.model_validate(u).model_dump(mode="json") for u in users],
        message=f"Retrieved {len(users)} user(s).",
    )
