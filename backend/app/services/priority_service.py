"""
app/services/priority_service.py

Combines urgency (the need score from need_score_service) with accessibility
(distance to the nearest shelter and hospital) into a single distribution
priority ranking.

Rationale
---------
A disaster can be extremely urgent but currently unreachable, or moderately
urgent but sitting right next to well-stocked responder assets. Objective:
"prioritize resource distribution based on urgency AND accessibility of
affected regions" — so distribution_priority_score weights need higher
(0.6) but lets accessibility (0.4) move a disaster up or down within that:
two disasters with similar need get the more reachable one served first,
since a coordinator can act on it immediately and with more certainty.

Accessibility is intentionally about "can we act right now" (closer = higher
score), not about "does this remote area deserve extra help" — that is a
legitimate alternative framing, but this platform doesn't have real transport
infrastructure data (road quality, terrain) that would be required to model
"hard to reach but needs pre-positioning" properly. Straight-line proximity to
existing responder assets is the honest signal available in this dataset.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.disaster import Disaster
from app.models.enums import DisasterStatus
from app.models.hospital import Hospital
from app.models.shelter import Shelter
from app.schemas.priority import DistributionPriorityResponse
from app.services.need_score_service import compute_need_score
from app.utils.geo import haversine_km

_WEIGHT_NEED = 0.6
_WEIGHT_ACCESSIBILITY = 0.4

# Distance at/beyond which accessibility bottoms out at 0.
_MAX_RELEVANT_DISTANCE_KM = 150.0

_NEUTRAL_ACCESSIBILITY_SCORE = 50.0


def _distance_score(distance_km: float) -> float:
    """Linear falloff: 0km -> 100, _MAX_RELEVANT_DISTANCE_KM+ -> 0."""
    fraction = max(0.0, min(1.0, distance_km / _MAX_RELEVANT_DISTANCE_KM))
    return round(100.0 * (1.0 - fraction), 1)


def _nearest(
    lat: float, lon: float, candidates: list, name_attr: str
) -> tuple[str, float] | None:
    """Return (name, distance_km) of the nearest candidate with coordinates, or None."""
    best: tuple[str, float] | None = None
    for c in candidates:
        if c.latitude is None or c.longitude is None:
            continue
        dist = haversine_km(lat, lon, c.latitude, c.longitude)
        if best is None or dist < best[1]:
            best = (getattr(c, name_attr), round(dist, 1))
    return best


def rank_by_distribution_priority(
    db: Session,
    include_resolved: bool = False,
) -> list[DistributionPriorityResponse]:
    """Compute and rank all active disasters by combined urgency + accessibility."""
    disaster_stmt = (
        select(Disaster)
        .where(Disaster.is_deleted.is_(False))
        .options(
            selectinload(Disaster.emergency_reports),
            selectinload(Disaster.resources),
        )
    )
    if not include_resolved:
        disaster_stmt = disaster_stmt.where(Disaster.status != DisasterStatus.RESOLVED)
    disasters = list(db.execute(disaster_stmt).scalars().all())

    shelters = list(
        db.execute(select(Shelter).where(Shelter.is_deleted.is_(False))).scalars().all()
    )
    hospitals = list(
        db.execute(select(Hospital).where(Hospital.is_deleted.is_(False))).scalars().all()
    )

    results: list[DistributionPriorityResponse] = []
    for disaster in disasters:
        need = compute_need_score(disaster)

        nearest_shelter = None
        nearest_hospital = None
        if disaster.latitude is not None and disaster.longitude is not None:
            nearest_shelter = _nearest(disaster.latitude, disaster.longitude, shelters, "shelter_name")
            nearest_hospital = _nearest(disaster.latitude, disaster.longitude, hospitals, "hospital_name")

        component_scores = []
        if nearest_shelter is not None:
            component_scores.append(_distance_score(nearest_shelter[1]))
        if nearest_hospital is not None:
            component_scores.append(_distance_score(nearest_hospital[1]))

        if component_scores:
            accessibility_score = round(sum(component_scores) / len(component_scores), 1)
            accessibility_data_available = True
        else:
            accessibility_score = _NEUTRAL_ACCESSIBILITY_SCORE
            accessibility_data_available = False

        distribution_priority_score = round(
            need.need_score * _WEIGHT_NEED + accessibility_score * _WEIGHT_ACCESSIBILITY, 1
        )

        results.append(
            DistributionPriorityResponse(
                disaster_id=disaster.id,
                title=disaster.title,
                disaster_type=disaster.disaster_type,
                severity=disaster.severity,
                status=disaster.status,
                district=disaster.district,
                state=disaster.state,
                need_score=need.need_score,
                nearest_shelter_name=nearest_shelter[0] if nearest_shelter else None,
                nearest_shelter_distance_km=nearest_shelter[1] if nearest_shelter else None,
                nearest_hospital_name=nearest_hospital[0] if nearest_hospital else None,
                nearest_hospital_distance_km=nearest_hospital[1] if nearest_hospital else None,
                accessibility_score=accessibility_score,
                accessibility_data_available=accessibility_data_available,
                distribution_priority_score=distribution_priority_score,
                rank=0,
            )
        )

    results.sort(key=lambda r: r.distribution_priority_score, reverse=True)
    for idx, item in enumerate(results, start=1):
        item.rank = idx

    return results
