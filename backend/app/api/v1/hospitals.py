"""
app/api/v1/hospitals.py

Hospital inventory & coordination router — framework skeleton.

Manages hospital records, bed capacity, medical resource inventory,
and coordinates patient intake during disaster events.

Prefix  : /api/v1/hospitals
Tags    : Hospitals
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_HOSPITALS

router = APIRouter(
    prefix="/hospitals",
    tags=[API_V1_TAG_HOSPITALS],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /hospitals/                    → Paginated list of all hospitals
# POST /hospitals/                    → Register a hospital in the system
# GET  /hospitals/available           → List hospitals with available beds
# GET  /hospitals/{hospital_id}       → Retrieve hospital details
# PUT  /hospitals/{hospital_id}       → Update hospital information or capacity
# DELETE /hospitals/{hospital_id}     → Remove a hospital from the registry
# GET  /hospitals/{hospital_id}/resources → List medical resources at a hospital
# POST /hospitals/{hospital_id}/capacity  → Report current capacity update
