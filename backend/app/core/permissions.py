"""
app/core/permissions.py

Production Role-Based Access Control (RBAC) dependency factory.

Usage — inline factory
----------------------
    @router.post("/restricted", dependencies=[Depends(require_role(RoleEnum.GOVERNMENT))])
    async def restricted_endpoint(): ...

Usage — named type aliases (recommended for clean signatures)
-------------------------------------------------------------
    from app.core.permissions import RequireGovernment

    @router.post("/declare-disaster")
    async def declare_disaster(current_user: RequireGovernment): ...

Available type aliases
----------------------
    RequireGovernment   — RoleEnum.GOVERNMENT only
    RequireNGO          — RoleEnum.NGO only
    RequireVolunteer    — RoleEnum.VOLUNTEER only
    RequireHospital     — RoleEnum.HOSPITAL only
    RequireCitizen      — RoleEnum.CITIZEN only
    RequireAdminRoles   — RoleEnum.GOVERNMENT or RoleEnum.NGO
    RequireFieldRoles   — RoleEnum.VOLUNTEER or RoleEnum.NGO or RoleEnum.HOSPITAL
    CurrentUser         — Any authenticated active user (re-exported from dependencies)

Design notes
------------
- `require_role()` returns an async inner function that FastAPI registers
  as a proper dependency (not just a decorator) — routes receive the
  authenticated User instance, not just None.
- Error responses are consistent:
    401 → invalid / missing credentials
    403 → valid credentials but insufficient role
- The dependency chain:
    oauth2_scheme → get_current_user → get_current_active_user → _role_guard

Circular import prevention
---------------------------
  This module imports from:
    - app.dependencies.auth   (imports from security + models only)
    - app.models.enums        (no imports from permissions)
    - app.models.user         (no imports from permissions)
    - app.core.roles          (existing module, no new imports)
  No imports from app.services or app.api.
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status

from app.core.roles import RoleHierarchy, UserRole
from app.dependencies.auth import CurrentUser, get_current_active_user
from app.models.enums import RoleEnum
from app.models.user import User


# ---------------------------------------------------------------------------
# Core RBAC dependency factory
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: RoleEnum) -> Callable:
    """
    Dependency factory that restricts access to users with one of the given roles.

    The inner function receives the current active user from the dependency chain
    and raises HTTP 403 if the user's role is not in the allowed set.

    Args:
        *allowed_roles: One or more RoleEnum members that may access the endpoint.

    Returns:
        An async FastAPI-compatible dependency callable that resolves to the User.

    Example::

        @router.post("/disasters", dependencies=[Depends(require_role(RoleEnum.GOVERNMENT))])
        async def create_disaster(): ...

        # Or returning the user:
        @router.get("/my-dashboard")
        async def dashboard(user: Annotated[User, Depends(require_role(RoleEnum.GOVERNMENT))]): ...
    """

    async def _role_guard(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            allowed_names = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Your role '{current_user.role.value}' is not "
                    f"authorised for this operation. "
                    f"Required role(s): [{allowed_names}]."
                ),
            )
        return current_user

    return _role_guard


def require_minimum_role(minimum_role: UserRole) -> Callable:
    """
    Dependency factory that allows access to users whose privilege level meets
    or exceeds the specified minimum.

    Uses the RoleHierarchy.LEVELS mapping from app.core.roles.
    Government (level 5) and NGO (level 4) automatically pass a Volunteer (2) check.

    Args:
        minimum_role: The minimum UserRole required.

    Returns:
        An async FastAPI-compatible dependency callable that resolves to the User.
    """

    async def _minimum_role_guard(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # Map RoleEnum to UserRole for hierarchy comparison
        try:
            user_role = UserRole(current_user.role.value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to determine role hierarchy for your account.",
            )

        if not RoleHierarchy.has_minimum_role(user_role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient privileges. "
                    f"Minimum required role: '{minimum_role.value}'. "
                    f"Your role: '{current_user.role.value}'."
                ),
            )
        return current_user

    return _minimum_role_guard


# ---------------------------------------------------------------------------
# Named type aliases — use in route signatures for clean, readable code
# ---------------------------------------------------------------------------

RequireGovernment = Annotated[User, Depends(require_role(RoleEnum.GOVERNMENT))]
"""Access restricted to Government users only."""

RequireNGO = Annotated[User, Depends(require_role(RoleEnum.NGO))]
"""Access restricted to NGO users only."""

RequireVolunteer = Annotated[User, Depends(require_role(RoleEnum.VOLUNTEER))]
"""Access restricted to Volunteer users only."""

RequireHospital = Annotated[User, Depends(require_role(RoleEnum.HOSPITAL))]
"""Access restricted to Hospital users only."""

RequireCitizen = Annotated[User, Depends(require_role(RoleEnum.CITIZEN))]
"""Access restricted to Citizen users only."""

RequireAdminRoles = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO)),
]
"""Access restricted to Government or NGO users (coordination-level roles)."""

RequireFieldRoles = Annotated[
    User,
    Depends(require_role(RoleEnum.VOLUNTEER, RoleEnum.NGO, RoleEnum.HOSPITAL)),
]
"""Access restricted to field-level roles: Volunteer, NGO, or Hospital."""

# Re-export CurrentUser from dependencies for single-import convenience
__all__ = [
    "require_role",
    "require_minimum_role",
    "RequireGovernment",
    "RequireNGO",
    "RequireVolunteer",
    "RequireHospital",
    "RequireCitizen",
    "RequireAdminRoles",
    "RequireFieldRoles",
    "CurrentUser",
]
