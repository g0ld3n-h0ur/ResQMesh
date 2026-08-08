"""
app/services/routing_service.py

Emergency Vehicle Routing & Dynamic Rerouting Engine.

Integrates OpenStreetMap-compatible routing (OSRM) with local road-closure detection,
geofencing checks, dynamic rerouting, and a demo/simulation mode.

Routing data is operational geographic data ONLY — strictly separate from ML training.
"""

from __future__ import annotations

import math
import logging
from typing import Any, Optional, Dict, List, Tuple
import httpx
from sqlalchemy.orm import Session

from app.models.road_closure import RoadClosure
from app.models.geofence import GeofenceZone
from app.models.audit_log import AuditLog

logger = logging.getLogger("app.services.routing")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in km between two geographic coordinates."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


def is_coordinate_in_geofence(
    lat: float, lon: float, zone_lat: float, zone_lon: float, radius_km: float
) -> bool:
    """Check if a coordinate falls within a circular geofenced zone."""
    dist = haversine_distance_km(lat, lon, zone_lat, zone_lon)
    return dist <= radius_km


def check_active_closures(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    db: Session,
) -> List[RoadClosure]:
    """Find active road closures along or near the route path."""
    closures = (
        db.query(RoadClosure)
        .filter(RoadClosure.is_active == True, RoadClosure.is_deleted == False)
        .all()
    )
    blocked: List[RoadClosure] = []
    # Midpoint and corridor approximation
    mid_lat = (origin_lat + dest_lat) / 2.0
    mid_lon = (origin_lon + dest_lon) / 2.0
    corridor_radius = max(
        2.0, haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon) / 1.5
    )

    for closure in closures:
        if haversine_distance_km(mid_lat, mid_lon, closure.latitude, closure.longitude) <= corridor_radius:
            blocked.append(closure)
    return blocked


def calculate_emergency_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    vehicle_type: str,
    db: Session,
    is_simulation: bool = False,
) -> Dict[str, Any]:
    """
    Calculate an emergency route using OpenStreetMap OSRM API with fallback,
    checking for active road blockages and dynamic rerouting.
    """
    direct_km = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
    blocked_segments = check_active_closures(origin_lat, origin_lon, dest_lat, dest_lon, db)

    # Base vehicle speeds (km/h)
    speed_kmh = {
        "ambulance": 65.0,
        "rescue_truck": 50.0,
        "boat": 25.0,
        "supply_van": 55.0,
    }.get(vehicle_type.lower(), 50.0)

    # Try OSRM public API with short timeout
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
    osrm_success = False
    route_geometry = None
    distance_km = direct_km * 1.3  # road factor fallback
    eta_minutes = round((distance_km / speed_kmh) * 60.0, 1)

    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(osrm_url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    r = data["routes"][0]
                    distance_km = round(r["distance"] / 1000.0, 2)
                    eta_minutes = round((r["duration"] / 60.0), 1)
                    route_geometry = r.get("geometry")
                    osrm_success = True
    except Exception as exc:
        logger.warning("OSRM API fallback used: %s", exc)

    if not route_geometry:
        route_geometry = {
            "type": "LineString",
            "coordinates": [[origin_lon, origin_lat], [dest_lon, dest_lat]],
        }

    # Handle dynamic rerouting if blocked segment detected
    if blocked_segments:
        blocked = blocked_segments[0]
        reroute_reason = f"Blocked road: {blocked.road_name} ({blocked.reason})"
        alt_distance_km = round(distance_km * 1.25, 2)
        alt_eta_minutes = round(eta_minutes * 1.3, 1)

        # Build modified bypass geometry
        bypass_lat = blocked.latitude + 0.02
        bypass_lon = blocked.longitude + 0.02
        alt_geometry = {
            "type": "LineString",
            "coordinates": [
                [origin_lon, origin_lat],
                [bypass_lon, bypass_lat],
                [dest_lon, dest_lat],
            ],
        }

        # Record audit event for rerouting
        audit = AuditLog(
            action="ROUTE_RECALCULATED",
            entity_type="RoadClosure",
            entity_id=str(blocked.id),
            previous_state={"route_distance_km": distance_km, "eta_minutes": eta_minutes},
            new_state={"alternate_distance_km": alt_distance_km, "alternate_eta_minutes": alt_eta_minutes, "reason": reroute_reason},
        )
        db.add(audit)
        db.commit()

        return {
            "status": "REROUTED",
            "is_rerouted": True,
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "vehicle_type": vehicle_type,
            "original_route": {
                "distance_km": distance_km,
                "eta_minutes": eta_minutes,
            },
            "blocked_segment": {
                "road_name": blocked.road_name,
                "reason": blocked.reason,
                "latitude": blocked.latitude,
                "longitude": blocked.longitude,
            },
            "alternate_route": {
                "distance_km": alt_distance_km,
                "eta_minutes": alt_eta_minutes,
                "geometry": alt_geometry,
            },
            "reroute_reason": reroute_reason,
            "provider": "OSRM (OpenStreetMap)" if osrm_success else "ResQMesh GIS Engine",
            "mode": "SIMULATION" if is_simulation else "OPERATIONAL",
        }

    return {
        "status": "SAFE_ROUTE",
        "is_rerouted": False,
        "origin": {"latitude": origin_lat, "longitude": origin_lon},
        "destination": {"latitude": dest_lat, "longitude": dest_lon},
        "vehicle_type": vehicle_type,
        "distance_km": distance_km,
        "eta_minutes": eta_minutes,
        "geometry": route_geometry,
        "blocked_segments": [],
        "provider": "OSRM (OpenStreetMap)" if osrm_success else "ResQMesh GIS Engine",
        "mode": "SIMULATION" if is_simulation else "OPERATIONAL",
    }
