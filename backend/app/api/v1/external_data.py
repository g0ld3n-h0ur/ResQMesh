"""
app/api/v1/external_data.py

External Situational Data router — consolidates live third-party data
(weather, earthquakes) with internal disaster records into one unified view.

Prefix : /api/v1/external-data
Tags   : External Data
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.disaster import Disaster
from app.models.enums import DisasterStatus
from app.schemas.external_data import UnifiedSituationalFeed
from app.services.external_data_service import get_unified_situational_feed
from app.utils.constants import API_V1_TAG_EXTERNAL_DATA
from app.utils.response import success_response

router = APIRouter(
    prefix="/external-data",
    tags=[API_V1_TAG_EXTERNAL_DATA],
)


@router.get(
    "/situational-feed",
    summary="Unified live situational feed (internal + external sources)",
    description="""
Merges live third-party data with the platform's own active disaster
records into a single, unified view:

- **Live weather** at each active disaster's coordinates, from Open-Meteo
  (temperature, humidity, precipitation, wind).
- **Recent significant earthquakes** worldwide (magnitude 4.5+, last 7 days),
  from the USGS Earthquake Hazards Program feed.

Both external sources are free and require no API key. If either is
unreachable, that part of the response is marked unavailable rather than
failing the whole request — internal disaster data is always returned.

No authentication required — read-only.
    """,
)
async def get_situational_feed(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    stmt = (
        select(Disaster)
        .where(Disaster.is_deleted.is_(False))
        .where(Disaster.status != DisasterStatus.RESOLVED)
    )
    disasters = list(db.execute(stmt).scalars().all())

    feed = await get_unified_situational_feed(disasters)
    validated = UnifiedSituationalFeed.model_validate(feed)
    return success_response(
        data=validated.model_dump(mode="json"),
        message=(
            f"Situational feed generated for {len(feed['disasters'])} active disaster(s), "
            f"{len(feed['recent_earthquakes'])} recent earthquake(s)."
        ),
    )
