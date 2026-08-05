"""
app/api/v1/hospital.py

Hospital user portal router — framework skeleton.

Handles hospital staff authentication context, capacity reporting,
patient intake tracking, and resource requests.

Prefix  : /api/v1/hospital
Tags    : Hospital
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_HOSPITAL

router = APIRouter(
    prefix="/hospital",
    tags=[API_V1_TAG_HOSPITAL],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /hospital/dashboard            → Hospital staff summary dashboard
# POST /hospital/capacity             → Update hospital capacity report
# GET  /hospital/patients             → List patients currently admitted
# POST /hospital/resource-request     → Submit a medical resource request
# GET  /hospital/resource-requests    → List submitted resource requests
