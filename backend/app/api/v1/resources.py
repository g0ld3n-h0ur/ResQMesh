"""
app/api/v1/resources.py

Resource management router — framework skeleton.

Tracks physical relief resources (food, water, medicine, equipment)
including inventory, allocation, and distribution logistics.

Prefix  : /api/v1/resources
Tags    : Resources
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_RESOURCES

router = APIRouter(
    prefix="/resources",
    tags=[API_V1_TAG_RESOURCES],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /resources/                    → Paginated list of all resources
# POST /resources/                    → Register a new resource item / batch
# GET  /resources/{resource_id}       → Retrieve a specific resource record
# PUT  /resources/{resource_id}       → Update resource details or quantity
# DELETE /resources/{resource_id}     → Remove / write-off a resource record
# POST /resources/{resource_id}/allocate → Allocate resource to a disaster zone
# GET  /resources/low-stock           → List resources below threshold quantity
