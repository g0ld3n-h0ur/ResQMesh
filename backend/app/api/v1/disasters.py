"""
app/api/v1/disasters.py

Disaster management router — framework skeleton.

Core domain router for creating, querying, and updating disaster events.
Integrates with AI prediction and resource allocation in future phases.

Prefix  : /api/v1/disasters
Tags    : Disasters
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_DISASTERS

router = APIRouter(
    prefix="/disasters",
    tags=[API_V1_TAG_DISASTERS],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /disasters/                  → Paginated list of all disaster events
# POST /disasters/                  → Create a new disaster event record
# GET  /disasters/active            → List currently active disasters
# GET  /disasters/{disaster_id}     → Retrieve a specific disaster by ID
# PUT  /disasters/{disaster_id}     → Update disaster details or status
# DELETE /disasters/{disaster_id}   → Archive / soft-delete a disaster record
# GET  /disasters/{disaster_id}/timeline → Full event timeline for a disaster
