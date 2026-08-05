"""
app/utils/constants.py

Application-wide constants.

Centralise magic strings, numeric limits, and configuration keys here
so they are never duplicated across the codebase.
"""

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
API_V1_TAG_AUTH = "Authentication"
API_V1_TAG_GOVERNMENT = "Government"
API_V1_TAG_NGO = "NGO"
API_V1_TAG_VOLUNTEER = "Volunteer"
API_V1_TAG_HOSPITAL = "Hospital"
API_V1_TAG_CITIZEN = "Citizen"
API_V1_TAG_DISASTERS = "Disasters"
API_V1_TAG_REPORTS = "Reports"
API_V1_TAG_PREDICTION = "AI Prediction"
API_V1_TAG_DASHBOARD = "Dashboard"
API_V1_TAG_RESOURCES = "Resources"
API_V1_TAG_SHELTERS = "Shelters"
API_V1_TAG_HOSPITALS = "Hospitals"
API_V1_TAG_NOTIFICATIONS = "Notifications"

# ---------------------------------------------------------------------------
# Disaster severity levels
# ---------------------------------------------------------------------------
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

SEVERITY_LEVELS = (SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL)

# ---------------------------------------------------------------------------
# Disaster status
# ---------------------------------------------------------------------------
DISASTER_STATUS_ACTIVE = "active"
DISASTER_STATUS_MONITORING = "monitoring"
DISASTER_STATUS_RESOLVED = "resolved"

DISASTER_STATUSES = (
    DISASTER_STATUS_ACTIVE,
    DISASTER_STATUS_MONITORING,
    DISASTER_STATUS_RESOLVED,
)

# ---------------------------------------------------------------------------
# Pagination defaults
# ---------------------------------------------------------------------------
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Date / time
# ---------------------------------------------------------------------------
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%Y-%m-%d"
