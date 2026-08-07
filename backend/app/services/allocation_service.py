"""
app/services/allocation_service.py

Suggests how to distribute currently unassigned, available relief resource
stock across active disasters — the "optimization approach for allocating
limited relief resources efficiently" objective.

Algorithm: weighted proportional apportionment (largest-remainder /
Hamilton method), the same class of method used for allocating fixed pools
of seats/goods fairly by weight. For each unassigned resource depot row:

  1. Weight each active disaster by its need score (see need_score_service).
  2. Give each disaster a quota = row_quantity * disaster_weight / total_weight.
  3. Assign each disaster floor(quota) units.
  4. Distribute the leftover units (from rounding down) one at a time to the
     disasters with the largest fractional remainder, until the row's full
     quantity is accounted for.

This guarantees every unit of available stock is assigned to someone (no
idle stock left unaccounted for in the suggestion) and that higher-need
disasters receive a proportionally larger share — a transparent, auditable
alternative to a human eyeballing which disaster "seems" more deserving.

This function only *suggests* — it does not write to the database. A
coordinator reviews the suggestions and applies the ones they agree with via
the existing POST /resources/{id}/allocate endpoint, which already validates
and only that endpoint mutates state.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ResourceStatus
from app.models.resource import Resource
from app.schemas.allocation_suggestion import AllocationSuggestionItem
from app.services.need_score_service import NeedScoreResponse, rank_disasters_by_need


def _apportion(total: int, weights: list[float]) -> list[int]:
    """
    Largest-remainder apportionment of `total` indivisible units across
    `weights`. Returns a list of integer shares, same length as weights,
    summing exactly to `total` (assuming total >= 0).
    """
    if total <= 0 or not weights:
        return [0] * len(weights)

    weight_sum = sum(weights)
    if weight_sum <= 0:
        # No disaster has any measurable need — nothing to suggest.
        return [0] * len(weights)

    quotas = [total * w / weight_sum for w in weights]
    shares = [int(q) for q in quotas]  # floor
    remainders = [q - s for q, s in zip(quotas, shares)]

    leftover = total - sum(shares)
    # Give the leftover units to the largest remainders first.
    order = sorted(range(len(weights)), key=lambda i: remainders[i], reverse=True)
    for i in order[:leftover]:
        shares[i] += 1

    return shares


def suggest_allocations(db: Session) -> list[AllocationSuggestionItem]:
    """
    Compute suggested allocations of every unassigned, available resource
    row across active disasters, weighted by need score.
    """
    ranked_disasters: list[NeedScoreResponse] = rank_disasters_by_need(db, include_resolved=False)
    if not ranked_disasters:
        return []

    weights = [d.need_score for d in ranked_disasters]

    resource_stmt = select(Resource).where(
        Resource.is_deleted.is_(False),
        Resource.status == ResourceStatus.AVAILABLE,
        Resource.assigned_disaster.is_(None),
        Resource.available_quantity > 0,
    )
    unassigned_resources = list(db.execute(resource_stmt).scalars().all())

    suggestions: list[AllocationSuggestionItem] = []
    for resource in unassigned_resources:
        shares = _apportion(resource.available_quantity, weights)
        total_weight = sum(weights) or 1.0

        for disaster, share in zip(ranked_disasters, shares):
            if share <= 0:
                continue
            pct = round(100 * disaster.need_score / total_weight, 1)
            suggestions.append(
                AllocationSuggestionItem(
                    resource_id=resource.id,
                    resource_type=resource.resource_type,
                    resource_location=resource.location,
                    source_available_quantity=resource.available_quantity,
                    disaster_id=disaster.disaster_id,
                    disaster_title=disaster.title,
                    disaster_need_rank=disaster.rank,
                    disaster_need_score=disaster.need_score,
                    suggested_quantity=share,
                    rationale=(
                        f"Ranked #{disaster.rank} by need (score {disaster.need_score}) — "
                        f"receives a {pct}% weighted share of this depot's "
                        f"{resource.available_quantity} available {resource.resource_type} unit(s)."
                    ),
                )
            )

    suggestions.sort(key=lambda s: (s.disaster_need_rank, s.resource_type))
    return suggestions
