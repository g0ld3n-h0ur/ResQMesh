"""
app/core/permissions.py

Permission guard factory for Role-Based Access Control (RBAC).

This module exposes FastAPI dependency callables that enforce role-based
access on protected routes. Full enforcement logic will be implemented
once the authentication service is in place.
"""

from typing import Callable

from fastapi import Depends, HTTPException, status

from app.core.roles import RoleHierarchy, UserRole
from app.core.security import oauth2_scheme


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory that restricts access to users with one of the given roles.

    Usage in a route:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])

    Args:
        *allowed_roles: One or more roles that are permitted to access the endpoint.

    Returns:
        A FastAPI-compatible dependency callable.
    """

    async def _role_guard(token: str = Depends(oauth2_scheme)) -> None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication and RBAC enforcement will be implemented in Phase 2.",
        )

    return _role_guard


def require_minimum_role(minimum_role: UserRole) -> Callable:
    """
    Dependency factory that allows access to users whose role meets or exceeds
    the specified minimum privilege level.

    Args:
        minimum_role: The minimum UserRole required to access the endpoint.

    Returns:
        A FastAPI-compatible dependency callable.
    """

    async def _minimum_role_guard(token: str = Depends(oauth2_scheme)) -> None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication and RBAC enforcement will be implemented in Phase 2.",
        )

    return _minimum_role_guard
