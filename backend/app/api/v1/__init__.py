"""
app/api/v1/__init__.py

Convenience re-exports for all v1 router modules.

Import individual routers directly from this package for clean registration
in app/main.py:

    from app.api.v1 import auth, disasters, ...
"""

from app.api.v1 import (
    auth,
    citizen,
    dashboard,
    disasters,
    government,
    hospital,
    hospitals,
    ngo,
    notifications,
    prediction,
    reports,
    resources,
    shelters,
    volunteer,
)

__all__ = [
    "auth",
    "citizen",
    "dashboard",
    "disasters",
    "government",
    "hospital",
    "hospitals",
    "ngo",
    "notifications",
    "prediction",
    "reports",
    "resources",
    "shelters",
    "volunteer",
]
