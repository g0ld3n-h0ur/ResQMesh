"""
app/services/__init__.py

Services package registry.

Business logic services are imported here for single-namespace access.
"""

from app.services import assignment_service  # noqa: F401
from app.services import auth_service  # noqa: F401
from app.services import dashboard_service  # noqa: F401
from app.services import disaster_service  # noqa: F401
from app.services import hospital_service  # noqa: F401
from app.services import notification_service  # noqa: F401
from app.services import prediction_service  # noqa: F401
from app.services import report_service  # noqa: F401
from app.services import resource_service  # noqa: F401
from app.services import shelter_service  # noqa: F401

__all__ = [
    "assignment_service",
    "auth_service",
    "dashboard_service",
    "disaster_service",
    "hospital_service",
    "notification_service",
    "prediction_service",
    "report_service",
    "resource_service",
    "shelter_service",
]
