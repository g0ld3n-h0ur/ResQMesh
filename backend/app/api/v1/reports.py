"""
app/api/v1/reports.py

Field reports router — framework skeleton.

Manages citizen and field-agent submitted incident and situation reports.
Reports feed the AI prediction pipeline and dashboard summaries.

Prefix  : /api/v1/reports
Tags    : Reports
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_REPORTS

router = APIRouter(
    prefix="/reports",
    tags=[API_V1_TAG_REPORTS],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# GET  /reports/                  → Paginated list of all reports
# POST /reports/                  → Submit a new field report
# GET  /reports/{report_id}       → Retrieve a specific report
# PUT  /reports/{report_id}       → Update / verify a report
# DELETE /reports/{report_id}     → Soft-delete / retract a report
# GET  /reports/disaster/{disaster_id} → All reports for a specific disaster
# POST /reports/{report_id}/verify    → Mark a report as verified by staff
