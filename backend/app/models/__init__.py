"""
app/models/__init__.py

Centralised model registry.

All ORM model classes are imported here so that:
  1. Alembic autogenerate discovers every table via Base.metadata.
  2. Application code can import models from a single namespace.
  3. SQLAlchemy's mapper registry is fully initialised at startup.
"""

# Core infrastructure
from app.models.base import BaseModel  # noqa: F401
from app.models.enums import (  # noqa: F401
    AnomalySeverity,
    AssignmentStatus,
    ClosureReason,
    DeliveryStatus,
    DisasterSeverity,
    DisasterStatus,
    FeatureFlag,
    GeofenceType,
    NotificationPriority,
    ProcurementStatus,
    ResourceStatus,
    RoleEnum,
    SubscriptionTier,
    VolunteerStatus,
)
from app.models.mixins import SoftDeleteMixin, TimestampMixin  # noqa: F401
from app.models.types import AutoJSON  # noqa: F401

# Leaf models
from app.models.anomaly import AnomalyRecord  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.csr import CSRProgram  # noqa: F401
from app.models.delivery import ProofOfDelivery  # noqa: F401
from app.models.geofence import GeofenceZone  # noqa: F401
from app.models.hospital import Hospital  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.procurement import ProcurementRequest  # noqa: F401
from app.models.road_closure import RoadClosure  # noqa: F401
from app.models.shelter import Shelter  # noqa: F401
from app.models.user import User  # noqa: F401

# Mid-tier models
from app.models.disaster import Disaster  # noqa: F401
from app.models.resource import Resource  # noqa: F401

# Dependent models
from app.models.emergency_report import EmergencyReport  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401

# Linking / junction models
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
    "SubscriptionTier",
    "FeatureFlag",
    "DeliveryStatus",
    "VolunteerStatus",
    "ProcurementStatus",
    "AnomalySeverity",
    "ClosureReason",
    "GeofenceType",
    # Domain models
    "User",
    "Organization",
    "Disaster",
    "EmergencyReport",
    "Prediction",
    "Resource",
    "Hospital",
    "Shelter",
    "Assignment",
    "Notification",
    "AuditLog",
    "CSRProgram",
    "ProofOfDelivery",
    "ProcurementRequest",
    "RoadClosure",
    "GeofenceZone",
    "AnomalyRecord",
]
