"""
app/services/external_data_service.py

Pulls live data from independent, free, keyless public APIs and merges it
with the platform's internal disaster data into one unified situational
feed — "consolidate fragmented disaster-related data from multiple sources
into a unified view."

Sources
-------
- USGS Earthquake Hazards Program — real-time significant-earthquake feed.
  https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson
  No API key, no rate-limit auth, updated every ~5 minutes by USGS.
- Open-Meteo — current weather conditions for any coordinate.
  https://open-meteo.com/en/docs
  No API key, free for non-commercial use.

Both calls are made concurrently with short timeouts and fail independently
and gracefully — an external outage degrades the feed (marks that source
unavailable) rather than breaking the endpoint or the rest of the platform.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger("app.services.external_data_service")

_TIMEOUT = httpx.Timeout(5.0, connect=3.0)

USGS_EARTHQUAKE_FEED_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"
)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_recent_earthquakes(limit: int = 10) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch recent significant earthquakes (magnitude 4.5+, last 7 days) from USGS.

    Returns (events, available). `available` is False on any network/parse
    failure — callers should treat an empty list + available=False as
    "source down", not "no earthquakes."
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(USGS_EARTHQUAKE_FEED_URL)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("USGS earthquake feed unavailable: %s", exc)
        return [], False

    events: list[dict[str, Any]] = []
    for feature in data.get("features", [])[:limit]:
        props = feature.get("properties", {}) or {}
        geom = feature.get("geometry", {}) or {}
        coords = geom.get("coordinates") or [None, None, None]
        event_time_ms = props.get("time")
        events.append(
            {
                "id": feature.get("id"),
                "place": props.get("place"),
                "magnitude": props.get("mag"),
                "time": (
                    datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)
                    if event_time_ms
                    else None
                ),
                "longitude": coords[0],
                "latitude": coords[1],
                "url": props.get("url"),
                "source": "USGS",
            }
        )
    return events, True


async def fetch_weather_snapshot(lat: float, lon: float) -> tuple[Optional[dict[str, Any]], bool]:
    """Fetch current weather conditions at a coordinate from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m",
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Open-Meteo weather fetch failed for (%s, %s): %s", lat, lon, exc)
        return None, False

    current = data.get("current")
    if not current:
        return None, False

    return (
        {
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "rain_mm": current.get("rain"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "observed_at": current.get("time"),
            "source": "Open-Meteo",
        },
        True,
    )


async def get_unified_situational_feed(disasters: list[Any]) -> dict[str, Any]:
    """
    Build the merged internal + external situational feed.

    Args:
        disasters: Active Disaster ORM instances (already queried by the caller).

    Fetches weather for every geolocated disaster and the earthquake feed
    concurrently rather than sequentially, so the total latency is roughly
    one round-trip, not N+1.
    """
    geolocated = [d for d in disasters if d.latitude is not None and d.longitude is not None]
    weather_tasks = [fetch_weather_snapshot(d.latitude, d.longitude) for d in geolocated]
    earthquake_task = fetch_recent_earthquakes()

    *weather_results, (earthquakes, earthquakes_available) = await asyncio.gather(
        *weather_tasks, earthquake_task
    )

    geolocated_ids = {d.id: i for i, d in enumerate(geolocated)}
    disaster_contexts: list[dict[str, Any]] = []
    for disaster in disasters:
        if disaster.id in geolocated_ids:
            weather, available = weather_results[geolocated_ids[disaster.id]]
        else:
            weather, available = None, False
        disaster_contexts.append(
            {
                "disaster_id": disaster.id,
                "title": disaster.title,
                "district": disaster.district,
                "state": disaster.state,
                "weather": weather,
                "weather_available": available,
            }
        )

    return {
        "disasters": disaster_contexts,
        "recent_earthquakes": earthquakes,
        "earthquakes_available": earthquakes_available,
        "generated_at": datetime.now(timezone.utc),
    }
