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
    BUSY = "busy"
    RESERVED = "reserved"
    DISPATCHED = "dispatched"
    UNAVAILABLE = "unavailable"
    ALLOCATED = "allocated"
    IN_TRANSIT = "in_transit"
    CONSUMED = "consumed"


# ---------------------------------------------------------------------------
# SaaS Subscription Tier
# ---------------------------------------------------------------------------
class SubscriptionTier(str, enum.Enum):
    """SaaS subscription plan tier."""

    PILOT = "pilot"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# ---------------------------------------------------------------------------
# SaaS Feature Flag
# ---------------------------------------------------------------------------
class FeatureFlag(str, enum.Enum):
    """SaaS feature flags for plan permissions."""

    AI = "ai"
    ANALYTICS = "analytics"
    AUDIT = "audit"
    CSR = "csr"
    ADVANCED_ROUTING = "advanced_routing"
    API_ACCESS = "api_access"
    TRANSPARENCY = "transparency"


# ---------------------------------------------------------------------------
# Delivery & Proof of Delivery Status
# ---------------------------------------------------------------------------
class DeliveryStatus(str, enum.Enum):
    """Post-disaster proof of delivery status."""

    SENT = "sent"
    RECEIVED = "received"
    VERIFIED = "verified"
    DISCREPANCY = "discrepancy"


# ---------------------------------------------------------------------------
# Volunteer Status
# ---------------------------------------------------------------------------
class VolunteerStatus(str, enum.Enum):
    """Volunteer availability and assignment status."""

    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"


# ---------------------------------------------------------------------------
# Procurement Status
# ---------------------------------------------------------------------------
class ProcurementStatus(str, enum.Enum):
    """Emergency procurement workflow status."""

    REQUESTED = "requested"
    APPROVED = "approved"
    PROCURED = "procured"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Anomaly Severity
# ---------------------------------------------------------------------------
class AnomalySeverity(str, enum.Enum):
    """Severity level of detected inventory or audit anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Road Closure Reason
# ---------------------------------------------------------------------------
class ClosureReason(str, enum.Enum):
    """Reason for road blockage or closure."""

    FLOOD = "flood"
    LANDSLIDE = "landslide"
    EARTHQUAKE = "earthquake"
    FALLEN_INFRASTRUCTURE = "fallen_infrastructure"
    EMERGENCY_CLOSURE = "emergency_closure"
    AUTHORITY_RESTRICTION = "authority_restriction"


# ---------------------------------------------------------------------------
# Geofence Zone Type
# ---------------------------------------------------------------------------
class GeofenceType(str, enum.Enum):
    """Geospatial zone classification."""

    DISASTER_ZONE = "disaster_zone"
    RESTRICTED_ZONE = "restricted_zone"
    EVACUATION_ZONE = "evacuation_zone"
    OPERATIONAL_ZONE = "operational_zone"
    NO_ENTRY_ZONE = "no_entry_zone"

