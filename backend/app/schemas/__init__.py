"""
app/schemas/__init__.py

Centralised schema registry.

Import all Pydantic v2 schemas here so that:
  1. API route handlers can import from app.schemas directly.
  2. OpenAPI schema generation discovers every model via FastAPI.
  3. Tests can import all schemas from a single namespace.
"""

from app.schemas.assignment import (  # noqa: F401
    AssignmentBase,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.auth import (  # noqa: F401
    LoginRequest,
    RefreshRequest,
    RegisterCitizenRequest,
    RegisterGovernmentRequest,
    RegisterHospitalRequest,
    RegisterNGORequest,
    RegisterVolunteerRequest,
    TokenResponse,
    UserRegisterBase,
)
from app.schemas.base import (  # noqa: F401
    BaseSchema,
    FullResponseSchema,
    IDSchema,
    TimestampSchema,
)
from app.schemas.disaster import (  # noqa: F401
    DisasterBase,
    DisasterCreate,
    DisasterResponse,
    DisasterUpdate,
)
from app.schemas.emergency_report import (  # noqa: F401
    EmergencyReportBase,
    EmergencyReportCreate,
    EmergencyReportResponse,
    EmergencyReportUpdate,
)
from app.schemas.hospital import (  # noqa: F401
    HospitalBase,
    HospitalCreate,
    HospitalResponse,
    HospitalUpdate,
)
from app.schemas.notification import (  # noqa: F401
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from app.schemas.prediction import (  # noqa: F401
    PredictionBase,
    PredictionCreate,
    PredictionResponse,
    PredictionUpdate,
)
from app.schemas.resource import (  # noqa: F401
    ResourceBase,
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
)
from app.schemas.shelter import (  # noqa: F401
    ShelterBase,
    ShelterCreate,
    ShelterResponse,
    ShelterUpdate,
)
from app.schemas.user import (  # noqa: F401
    UserBase,
    UserCreate,
    UserPublicResponse,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Base
    "BaseSchema",
    "IDSchema",
    "TimestampSchema",
    "FullResponseSchema",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPublicResponse",
    # Disaster
    "DisasterBase",
    "DisasterCreate",
    "DisasterUpdate",
    "DisasterResponse",
    # EmergencyReport
    "EmergencyReportBase",
    "EmergencyReportCreate",
    "EmergencyReportUpdate",
    "EmergencyReportResponse",
    # Prediction
    "PredictionBase",
    "PredictionCreate",
    "PredictionUpdate",
    "PredictionResponse",
    # Resource
    "ResourceBase",
    "ResourceCreate",
    "ResourceUpdate",
    "ResourceResponse",
    # Hospital
    "HospitalBase",
    "HospitalCreate",
    "HospitalUpdate",
    "HospitalResponse",
    # Shelter
    "ShelterBase",
    "ShelterCreate",
    "ShelterUpdate",
    "ShelterResponse",
    # Assignment
    "AssignmentBase",
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentResponse",
    # Notification
    "NotificationBase",
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    # Auth
    "TokenResponse",
    "UserRegisterBase",
    "RegisterGovernmentRequest",
    "RegisterNGORequest",
    "RegisterVolunteerRequest",
    "RegisterHospitalRequest",
    "RegisterCitizenRequest",
    "LoginRequest",
    "RefreshRequest",
]

