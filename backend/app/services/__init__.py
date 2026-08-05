"""
app/services/__init__.py

Services package registry.

Business logic services are imported here for single-namespace access.
"""

from app.services import auth_service  # noqa: F401
from app.services import disaster_service  # noqa: F401

__all__ = [
    "auth_service",
    "disaster_service",
]


