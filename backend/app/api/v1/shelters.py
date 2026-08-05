"""
app/api/v1/shelters.py

Shelter management router — framework skeleton.

Manages emergency shelter locations, capacities, occupancy, and
availability for displaced citizens.

Prefix  : /api/v1/shelters
Tags    : Shelters
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_SHELTERS

router = APIRouter(
    prefix="/shelters",
    tags=[API_V1_TAG_SHELTERS],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /shelters/                    → Paginated list of all shelters
# POST /shelters/                    → Register a new shelter location
# GET  /shelters/available           → List shelters with available capacity
# GET  /shelters/{shelter_id}        → Retrieve a specific shelter record
# PUT  /shelters/{shelter_id}        → Update shelter details or capacity
# DELETE /shelters/{shelter_id}      → Decommission a shelter
# POST /shelters/{shelter_id}/checkin  → Check citizens into a shelter
# POST /shelters/{shelter_id}/checkout → Check citizens out of a shelter
