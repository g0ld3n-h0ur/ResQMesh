"""
app/api/v1/volunteer.py

Volunteer management router — framework skeleton.

Handles volunteer registration, skill-based assignment, availability
tracking, and task dispatch.

Prefix  : /api/v1/volunteers
Tags    : Volunteer
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_VOLUNTEER

router = APIRouter(
    prefix="/volunteers",
    tags=[API_V1_TAG_VOLUNTEER],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /volunteers/                 → List all volunteers
# POST /volunteers/register         → Register a new volunteer
# GET  /volunteers/{volunteer_id}   → Retrieve a volunteer's profile
# PUT  /volunteers/{volunteer_id}   → Update a volunteer's information
# POST /volunteers/{volunteer_id}/availability → Set availability status
# GET  /volunteers/available        → List currently available volunteers
# POST /volunteers/{volunteer_id}/assign → Assign volunteer to a disaster task
