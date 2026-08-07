"""
app/services/need_score_service.py

Computes a composite "need score" (0-100) per disaster, combining several
independent signals already present in the platform's data into a single
ranked priority list. This is a transparent, explainable formula rather
than a black-box model — every component is visible in the API response
so a coordinator can see *why* a disaster ranked where it did.

Why this exists
----------------
`Disaster.severity` alone is a single value a government user sets by hand
when the record is created — it never changes automatically as the
situation evolves. This service derives a second, continuously-updated
signal from real activity in the system:

  - severity_component (weight 0.35)
        The official human-assessed severity, as a baseline.
  - report_pressure_component (weight 0.30)
        Volume of citizen emergency reports linked to the disaster —
        more independently reported distress signals imply more people
        are actively affected right now.
  - resource_shortfall_component (weight 0.25)
        How depleted the resources assigned to this disaster are.
        A disaster with no resources assigned yet scores the maximum
        (100) here — nothing has been provisioned. A disaster whose
        assigned stock is heavily drawn down also scores high — supply
        is struggling to keep up with demand.
  - status_urgency_component (weight 0.10)
        Where the disaster sits in its response lifecycle. Freshly
        reported/unverified disasters score highest (nothing has
        happened yet); resolved disasters score zero.

The weighted sum is clamped to [0, 100] and bucketed into a need_level
(low/medium/high/critical) using the same thresholds the platform already
uses for severity, so the output is easy to compare against the manual
severity field.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.disaster import Disaster
from app.models.enums import DisasterSeverity, DisasterStatus
from app.schemas.need_score import NeedScoreBreakdown, NeedScoreResponse

# ---------------------------------------------------------------------------
# Component weights (must sum to 1.0)
# ---------------------------------------------------------------------------
_WEIGHT_SEVERITY = 0.35
_WEIGHT_REPORT_PRESSURE = 0.30
_WEIGHT_RESOURCE_SHORTFALL = 0.25
_WEIGHT_STATUS_URGENCY = 0.10

_SEVERITY_SCORES: dict[DisasterSeverity, float] = {
    DisasterSeverity.LOW: 20.0,
    DisasterSeverity.MEDIUM: 45.0,
    DisasterSeverity.HIGH: 70.0,
    DisasterSeverity.CRITICAL: 95.0,
}

_STATUS_URGENCY_SCORES: dict[DisasterStatus, float] = {
    DisasterStatus.REPORTED: 100.0,
    DisasterStatus.VERIFIED: 85.0,
    DisasterStatus.RESCUE_ONGOING: 70.0,
    DisasterStatus.RESOURCE_ALLOCATED: 55.0,
    DisasterStatus.RESOLVED: 0.0,
}

# Each linked report adds this many points to report_pressure, saturating at 100.
_POINTS_PER_REPORT = 20.0

_NEED_LEVEL_THRESHOLDS: list[tuple[float, str]] = [
    (80.0, "critical"),
    (60.0, "high"),
    (35.0, "medium"),
]


def _report_pressure_component(report_count: int) -> float:
    return min(100.0, report_count * _POINTS_PER_REPORT)


def _resource_shortfall_component(resources: list) -> float:
    if not resources:
        # Nothing provisioned yet — maximum unmet need.
        return 100.0
    total_quantity = sum(r.quantity for r in resources)
    total_available = sum(r.available_quantity for r in resources)
    if total_quantity <= 0:
        return 100.0
    depleted_fraction = 1.0 - (total_available / total_quantity)
    return max(0.0, min(100.0, depleted_fraction * 100.0))


def _need_level(score: float) -> str:
    for threshold, label in _NEED_LEVEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "low"


def compute_need_score(disaster: Disaster) -> NeedScoreResponse:
    """
    Compute the need score for a single Disaster ORM instance.

    Expects `disaster.emergency_reports` and `disaster.resources` to already
    be loaded (eager-loaded by the caller) to avoid per-disaster N+1 queries.
    """
    reports = disaster.emergency_reports or []
    resources = disaster.resources or []

    severity_component = _SEVERITY_SCORES.get(disaster.severity, 50.0)
    report_pressure_component = _report_pressure_component(len(reports))
    resource_shortfall_component = _resource_shortfall_component(resources)
    status_urgency_component = _STATUS_URGENCY_SCORES.get(disaster.status, 50.0)

    need_score = (
        severity_component * _WEIGHT_SEVERITY
        + report_pressure_component * _WEIGHT_REPORT_PRESSURE
        + resource_shortfall_component * _WEIGHT_RESOURCE_SHORTFALL
        + status_urgency_component * _WEIGHT_STATUS_URGENCY
    )
    need_score = round(max(0.0, min(100.0, need_score)), 1)

    return NeedScoreResponse(
        disaster_id=disaster.id,
        title=disaster.title,
        disaster_type=disaster.disaster_type,
        severity=disaster.severity,
        status=disaster.status,
        district=disaster.district,
        state=disaster.state,
        report_count=len(reports),
        resources_assigned=len(resources),
        need_score=need_score,
        need_level=_need_level(need_score),
        rank=0,  # filled in by rank_disasters_by_need after sorting
        breakdown=NeedScoreBreakdown(
            severity_component=round(severity_component * _WEIGHT_SEVERITY, 1),
            report_pressure_component=round(report_pressure_component * _WEIGHT_REPORT_PRESSURE, 1),
            resource_shortfall_component=round(resource_shortfall_component * _WEIGHT_RESOURCE_SHORTFALL, 1),
            status_urgency_component=round(status_urgency_component * _WEIGHT_STATUS_URGENCY, 1),
        ),
    )


def rank_disasters_by_need(
    db: Session,
    include_resolved: bool = False,
) -> list[NeedScoreResponse]:
    """
    Compute and rank need scores for all active (non-deleted) disasters.

    By default excludes RESOLVED disasters, since a resolved event no
    longer needs prioritisation against active ones.
    """
    stmt = (
        select(Disaster)
        .where(Disaster.is_deleted.is_(False))
        .options(
            selectinload(Disaster.emergency_reports),
            selectinload(Disaster.resources),
        )
    )
    if not include_resolved:
        stmt = stmt.where(Disaster.status != DisasterStatus.RESOLVED)

    disasters = list(db.execute(stmt).scalars().all())
    scored = [compute_need_score(d) for d in disasters]
    scored.sort(key=lambda s: s.need_score, reverse=True)

    for idx, item in enumerate(scored, start=1):
        item.rank = idx

    return scored
