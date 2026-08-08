"""
app/api/v1/government.py

Government portal router — framework skeleton.

Handles government-role specific operations such as issuing official
disaster declarations, releasing resources, and viewing coordination reports.

Prefix  : /api/v1/government
Tags    : Government
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_GOVERNMENT

router = APIRouter(
    prefix="/government",
    tags=[API_V1_TAG_GOVERNMENT],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /government/dashboard              → Government summary dashboard
# POST /government/disaster-declarations  → Issue a disaster declaration
# GET  /government/reports                → View all coordination reports
# PUT  /government/resources/allocate     → Allocate resources to a region
# GET  /government/agencies               → List registered government agencies
