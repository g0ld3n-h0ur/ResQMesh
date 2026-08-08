"""
app/api/v1/routing.py

Emergency Vehicle Routing, Road Blockages, Geofencing & Dynamic Rerouting router.

Prefix: /api/v1/routing
Tags: Routing & GIS
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.road_closure import RoadClosure
from app.models.geofence import GeofenceZone
from app.services.routing_service import calculate_emergency_route
from app.utils.response import success_response

router = APIRouter(
    prefix="/routing",
    tags=["Routing & GIS"],
)


class RouteRequest(BaseModel):
    origin_latitude: float = Field(..., ge=-90.0, le=90.0, examples=[12.9716])
    origin_longitude: float = Field(..., ge=-180.0, le=180.0, examples=[77.5946])
    destination_latitude: float = Field(..., ge=-90.0, le=90.0, examples=[13.0827])
    destination_longitude: float = Field(..., ge=-180.0, le=180.0, examples=[80.2707])
    vehicle_type: str = Field("ambulance", examples=["ambulance"])
    is_simulation: bool = Field(False, description="Enable demo simulation mode")


class RoadClosureCreate(BaseModel):
    road_name: str = Field(..., examples=["NH-44 Expressway Bridge"])
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_meters: float = Field(500.0, ge=10.0)
    reason: str = Field("flood", examples=["flood"])


class GeofenceCreate(BaseModel):
    name: str = Field(..., examples=["District 4 Evacuation Zone"])
    zone_type: str = Field("disaster_zone", examples=["disaster_zone"])
    center_latitude: float = Field(...)
    center_longitude: float = Field(...)
    radius_km: float = Field(5.0, ge=0.1)


@router.post("/calculate-route", summary="Calculate emergency vehicle route")
async def calculate_route(
    payload: RouteRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    result = calculate_emergency_route(
        origin_lat=payload.origin_latitude,
        origin_lon=payload.origin_longitude,
        dest_lat=payload.destination_latitude,
        dest_lon=payload.destination_longitude,
        vehicle_type=payload.vehicle_type,
        db=db,
        is_simulation=payload.is_simulation,
    )
    if result.get("status") == "NO_SAFE_ROUTE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NO_SAFE_ROUTE: All available paths are blocked by active road closures.",
        )
    return success_response(data=result, message="Emergency route calculated successfully.")


@router.post("/road-closures", summary="Create active road blockage")
async def create_road_closure(
    payload: RoadClosureCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    closure = RoadClosure(
        road_name=payload.road_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_meters=payload.radius_meters,
        reason=payload.reason,
        is_active=True,
    )
    db.add(closure)
    db.commit()
    db.refresh(closure)
    return success_response(
        data={"id": str(closure.id), "road_name": closure.road_name, "reason": closure.reason},
        message="Road closure registered successfully. Dynamic rerouting activated.",
    )


@router.get("/road-closures", summary="List active road closures")
async def list_road_closures(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    closures = db.query(RoadClosure).filter(RoadClosure.is_active == True, RoadClosure.is_deleted == False).all()
    data = [
        {
            "id": str(c.id),
            "road_name": c.road_name,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "radius_meters": c.radius_meters,
            "reason": c.reason,
        }
        for c in closures
    ]
    return success_response(data=data, message="Active road closures retrieved.")


@router.post("/geofences", summary="Create geofenced zone")
async def create_geofence(
    payload: GeofenceCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    zone = GeofenceZone(
        name=payload.name,
        zone_type=payload.zone_type,
        center_latitude=payload.center_latitude,
        center_longitude=payload.center_longitude,
        radius_km=payload.radius_km,
        is_active=True,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return success_response(
        data={"id": str(zone.id), "name": zone.name, "zone_type": zone.zone_type},
        message="Geofence zone created successfully.",
    )
