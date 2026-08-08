"""
app/api/v1/commander.py

AI Disaster Commander Action Plan router.

Prefix: /api/v1/commander
Tags: AI Disaster Commander
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.action_plan_service import generate_action_plan
from app.utils.response import success_response

router = APIRouter(
    prefix="/commander",
    tags=["AI Disaster Commander"],
)


class ActionPlanRequest(BaseModel):
    disaster_type: str = Field("Flood", examples=["Flood"])
    severity_level: str = Field("High", examples=["High"])
    population_affected: int = Field(5000, ge=0, examples=[5000])
    households_affected: int = Field(1200, ge=0, examples=[1200])
    infrastructure_damage_score: float = Field(50.0, ge=0.0, le=100.0)
    nearest_relief_center_distance_km: float = Field(10.0, ge=0.0)
    available_volunteers: int = Field(30, ge=0)
    medical_teams_available: int = Field(3, ge=0)
    food_stock_kg: float = Field(500.0, ge=0.0)
    water_stock_liters: float = Field(2000.0, ge=0.0)
    shelter_capacity: float = Field(300.0, ge=0.0)
    funding_available_usd: float = Field(25000.0, ge=0.0)
    vulnerability_index: float = Field(0.5, ge=0.0, le=1.0)
    ngo_present: bool = Field(True)
    government_response_active: bool = Field(True)
    accessibility_status: str = Field("Accessible", examples=["Accessible"])
    communication_status: str = Field("Full", examples=["Full"])
    power_status: str = Field("Partial", examples=["Partial"])
    latitude: Optional[float] = Field(12.9716, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(77.5946, ge=-180.0, le=180.0)


@router.post("/action-plan", summary="Generate AI Disaster Commander Action Plan")
async def create_action_plan(
    payload: ActionPlanRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    incident_data = payload.model_dump()
    plan = generate_action_plan(
        incident_data=incident_data,
        db=db,
        origin_lat=payload.latitude,
        origin_lon=payload.longitude,
    )
    return success_response(
        data=plan,
        message="Action Plan synthesised successfully across ML PREDICTION, RULE-BASED CALCULATION, and ROUTING RESULT layers.",
    )
