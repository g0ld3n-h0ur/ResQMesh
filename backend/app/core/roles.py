"""
app/core/roles.py

Role definitions for Role-Based Access Control (RBAC).

Roles are defined as an enum to ensure type-safety throughout the application.
RBAC enforcement logic will be wired in future phases via the permissions module.
"""

from enum import Enum


class UserRole(str, Enum):
    """Enumeration of all user roles in the platform."""

    ADMIN = "admin"
    GOVERNMENT = "government"
    NGO = "ngo"
    VOLUNTEER = "volunteer"
    HOSPITAL = "hospital"
    CITIZEN = "citizen"


class RoleHierarchy:
    """
    Defines hierarchical privilege levels for roles.

    Higher numeric values indicate greater privilege.
    Used by the permissions layer to resolve access rights.
    """

    LEVELS: dict[UserRole, int] = {
        UserRole.CITIZEN: 1,
        UserRole.VOLUNTEER: 2,
        UserRole.HOSPITAL: 3,
        UserRole.NGO: 4,
        UserRole.GOVERNMENT: 5,
        UserRole.ADMIN: 10,
    }

    @classmethod
    def get_level(cls, role: UserRole) -> int:
        """Return the privilege level for the given role."""
        return cls.LEVELS.get(role, 0)

    @classmethod
    def has_minimum_role(cls, role: UserRole, minimum: UserRole) -> bool:
        """Return True if the given role meets or exceeds the minimum level."""
        return cls.get_level(role) >= cls.get_level(minimum)
