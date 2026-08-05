"""
app/models/__init__.py

Centralised model registry.

All ORM model classes are imported here so that:
  1. Alembic autogenerate discovers every table via Base.metadata.
  2. Application code can import models from a single namespace.
  3. SQLAlchemy's mapper registry is fully initialised at startup.

Import order follows the dependency graph (leaf nodes first):
  enums → types → mixins → base → leaf models → dependent models → linking models
"""

# Core infrastructure
from app.models.base import BaseModel  # noqa: F401
from app.models.enums import (  # noqa: F401
    AssignmentStatus,
    DisasterSeverity,
    DisasterStatus,
    NotificationPriority,
    ResourceStatus,
    RoleEnum,
)
from app.models.mixins import SoftDeleteMixin, TimestampMixin  # noqa: F401
from app.models.types import AutoJSON  # noqa: F401

# Leaf models (no incoming FK dependencies from other domain models)
from app.models.hospital import Hospital  # noqa: F401
from app.models.shelter import Shelter  # noqa: F401
from app.models.user import User  # noqa: F401

# Mid-tier models (depend on User)
from app.models.disaster import Disaster  # noqa: F401
from app.models.resource import Resource  # noqa: F401

# Dependent models (depend on Disaster)
from app.models.emergency_report import EmergencyReport  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401

# Linking / junction models (depend on multiple tables)
from app.models.assignment import Assignment  # noqa: F401
from app.models.notification import Notification  # noqa: F401

__all__ = [
    # Infrastructure
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AutoJSON",
    # Enums
    "RoleEnum",
    "DisasterSeverity",
    "DisasterStatus",
    "NotificationPriority",
    "AssignmentStatus",
    "ResourceStatus",
    # Domain models
    "User",
    "Disaster",
    "EmergencyReport",
    "Prediction",
    "Resource",
    "Hospital",
    "Shelter",
    "Assignment",
    "Notification",
]
