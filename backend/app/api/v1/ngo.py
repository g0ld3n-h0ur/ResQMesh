"""
app/api/v1/ngo.py

NGO (Non-Governmental Organisation) portal router — framework skeleton.

Handles NGO-role specific operations such as registration, volunteer
coordination, aid distribution tracking, and field reporting.

Prefix  : /api/v1/ngo
Tags    : NGO
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_NGO

router = APIRouter(
    prefix="/ngo",
    tags=[API_V1_TAG_NGO],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /ngo/dashboard          → NGO summary dashboard
# POST /ngo/register           → Register a new NGO
# GET  /ngo/list               → List all registered NGOs
# GET  /ngo/{ngo_id}           → Retrieve a specific NGO profile
# PUT  /ngo/{ngo_id}           → Update NGO profile information
# POST /ngo/{ngo_id}/volunteers → Assign volunteers to this NGO
# GET  /ngo/{ngo_id}/reports   → View field reports submitted by this NGO
