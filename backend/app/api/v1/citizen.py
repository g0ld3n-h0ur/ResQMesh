"""
app/api/v1/citizen.py

Citizen portal router — framework skeleton.

Handles citizen-facing operations such as submitting distress reports,
locating shelters, finding hospitals, and receiving emergency notifications.

Prefix  : /api/v1/citizens
Tags    : Citizen
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_CITIZEN

router = APIRouter(
    prefix="/citizens",
    tags=[API_V1_TAG_CITIZEN],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /citizens/me                  → Retrieve the authenticated citizen profile
# PUT  /citizens/me                  → Update citizen profile information
# POST /citizens/sos                 → Submit an emergency SOS distress signal
# GET  /citizens/shelters/nearby     → Find nearby open shelters
# GET  /citizens/hospitals/nearby    → Find nearby hospitals with capacity
# GET  /citizens/alerts              → Retrieve active alerts for the citizen's area
