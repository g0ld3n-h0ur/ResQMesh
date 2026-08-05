"""
app/api/v1/dashboard.py

Analytics dashboard router — framework skeleton.

Aggregates data from disasters, resources, volunteers, and reports
to serve summary metrics to the React frontend dashboard views.

Prefix  : /api/v1/dashboard
Tags    : Dashboard
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_DASHBOARD

router = APIRouter(
    prefix="/dashboard",
    tags=[API_V1_TAG_DASHBOARD],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET /dashboard/overview           → Platform-wide summary statistics
# GET /dashboard/active-disasters   → Count and list of active disasters
# GET /dashboard/resource-status    → Aggregated resource availability
# GET /dashboard/volunteer-stats    → Volunteer engagement statistics
# GET /dashboard/shelter-capacity   → Shelter occupancy summary
# GET /dashboard/recent-activity    → Latest events feed across the platform
