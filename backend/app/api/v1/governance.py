"""
app/api/v1/governance.py

Governance, Audit, Anomalies, SLA Analytics & Preparedness router.

Prefix: /api/v1/governance
Tags: Governance & Analytics
"""

from __future__ import annotations

from typing import Annotated, Any, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.audit_service import get_audit_logs
from app.services.anomaly_service import run_anomaly_checks
from app.services.escalation_service import run_escalation_checks
from app.services.analytics_service import (
    calculate_sla_analytics,
    generate_executive_situation_report,
    generate_after_action_review,
)
from app.services.preparedness_service import run_preparedness_simulation
from app.utils.response import success_response

router = APIRouter(
    prefix="/governance",
    tags=["Governance & Analytics"],
)


class PreparednessSimulationRequest(BaseModel):
    disaster_type: str = Field("Flood", examples=["Flood"])
    severity_level: str = Field("High", examples=["High"])
    population_affected: int = Field(10000, ge=0)
    households_affected: int = Field(2500, ge=0)
    infrastructure_damage_score: float = Field(60.0, ge=0.0, le=100.0)
    nearest_relief_center_distance_km: float = Field(15.0, ge=0.0)
    available_volunteers: int = Field(40, ge=0)
    medical_teams_available: int = Field(4, ge=0)
    food_stock_kg: float = Field(1000.0, ge=0.0)
    water_stock_liters: float = Field(4000.0, ge=0.0)
    shelter_capacity: float = Field(500.0, ge=0.0)
    funding_available_usd: float = Field(50000.0, ge=0.0)
    vulnerability_index: float = Field(0.6, ge=0.0, le=1.0)
    ngo_present: bool = Field(True)
    government_response_active: bool = Field(True)
    accessibility_status: str = Field("Accessible")
    communication_status: str = Field("Full")
    power_status: str = Field("Partial")


@router.get("/audit-trail", summary="Retrieve digital audit trail")
async def read_audit_trail(
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> Any:
    logs = get_audit_logs(db, limit=limit)
    data = [
        {
            "id": str(l.id),
            "actor_id": str(l.actor_id) if l.actor_id else None,
            "actor_role": l.actor_role,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "previous_state": l.previous_state,
            "new_state": l.new_state,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
    return success_response(data=data, message="Digital audit trail retrieved.")


@router.post("/anomalies/run-checks", summary="Run deterministic rule-based anomaly detection")
async def trigger_anomaly_checks(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    anomalies = run_anomaly_checks(db)
    return success_response(data=anomalies, message=f"Anomaly detection complete. {len(anomalies)} anomalies identified.")


@router.post("/escalations/run-checks", summary="Trigger automatic rule-based escalation checks")
async def trigger_escalation_checks(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    escalations = run_escalation_checks(db)
    return success_response(data=escalations, message=f"Escalation checks complete. {len(escalations)} incidents escalated.")


@router.get("/analytics/sla", summary="Get SLA and response analytics")
async def get_sla_metrics(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    metrics = calculate_sla_analytics(db)
    return success_response(data=metrics, message="SLA analytics calculated using actual database timestamps.")


@router.get("/reports/executive-situation", summary="Generate Executive Situation Report")
async def get_situation_report(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    report = generate_executive_situation_report(db)
    return success_response(data=report, message="Executive situation report generated.")


@router.get("/reports/after-action-review/{disaster_id}", summary="Generate After-Action Review (AAR)")
async def get_aar(
    disaster_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    aar = generate_after_action_review(db, disaster_id)
    return success_response(data=aar, message="After-Action Review generated.")


@router.post("/simulator/preparedness", summary="Run Disaster Preparedness Simulator")
async def run_preparedness_sim(
    payload: PreparednessSimulationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    sim_res = run_preparedness_simulation(payload.model_dump(), db)
    return success_response(data=sim_res, message="Disaster Preparedness Simulation completed.")
