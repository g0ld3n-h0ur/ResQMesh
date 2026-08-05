"""
app/models/enums.py

Shared enum definitions used across SQLAlchemy ORM models and Pydantic schemas.

All enums inherit from (str, enum.Enum) to ensure:
  - Direct JSON serialisation without custom encoders
  - Pydantic v2 compatibility out of the box
  - SQLAlchemy SAEnum column storage as VARCHAR strings
"""

import enum


# ---------------------------------------------------------------------------
# User Roles
# ---------------------------------------------------------------------------
class RoleEnum(str, enum.Enum):
    """Platform user role. Determines access level and dashboard routing."""

    GOVERNMENT = "government"
    NGO = "ngo"
    VOLUNTEER = "volunteer"
    HOSPITAL = "hospital"
    CITIZEN = "citizen"


# ---------------------------------------------------------------------------
# Disaster Severity
# ---------------------------------------------------------------------------
class DisasterSeverity(str, enum.Enum):
    """Impact severity level of a disaster event."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Disaster Lifecycle Status
# ---------------------------------------------------------------------------
class DisasterStatus(str, enum.Enum):
    """Current operational status in the disaster response lifecycle."""

    REPORTED = "reported"
    VERIFIED = "verified"
    RESOURCE_ALLOCATED = "resource_allocated"
    RESCUE_ONGOING = "rescue_ongoing"
    RESOLVED = "resolved"


# ---------------------------------------------------------------------------
# Notification Priority
# ---------------------------------------------------------------------------
class NotificationPriority(str, enum.Enum):
    """Priority level for platform alert notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Assignment Status
# ---------------------------------------------------------------------------
class AssignmentStatus(str, enum.Enum):
    """Lifecycle status of a resource / volunteer assignment."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Resource Status
# ---------------------------------------------------------------------------
class ResourceStatus(str, enum.Enum):
    """Operational status of a relief resource item."""

    AVAILABLE = "available"
    ALLOCATED = "allocated"
    IN_TRANSIT = "in_transit"
    CONSUMED = "consumed"
