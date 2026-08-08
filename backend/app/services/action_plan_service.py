"""
app/services/action_plan_service.py

AI Disaster Commander — Synthesis & Action Plan Generation Engine.

Synthesises three strictly separated layers:
  1. ML PREDICTION       — Priority label & recommended relief units from dataset-trained model.
  2. RULE-BASED CALCULATION — Inventory matching, nearest shelter/hospital capacity gaps.
  3. ROUTING RESULT       — GIS road distance, ETA, and dynamic rerouting around blockages.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from ml.predict import predict_allocation_priority, predict_relief_units
from app.models.hospital import Hospital
from app.models.shelter import Shelter
from app.models.resource import Resource
from app.services.routing_service import calculate_emergency_route, haversine_distance_km

logger = logging.getLogger("app.services.action_plan")


def generate_action_plan(
    incident_data: Dict[str, Any],
    db: Session,
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Generate a complete disaster response action plan.
    """
    # -----------------------------------------------------------------------
    # Layer 1: ML PREDICTION
    # -----------------------------------------------------------------------
    ml_priority = predict_allocation_priority(incident_data)
    ml_relief = predict_relief_units(incident_data)

    ml_output = {
        "layer_type": "ML PREDICTION",
        "allocation_priority": ml_priority.get("allocation_priority"),
        "confidence": ml_priority.get("confidence"),
        "class_probabilities": ml_priority.get("class_probabilities"),
        "recommended_relief_units": ml_relief.get("recommended_relief_units"),
        "models_used": [ml_priority.get("model"), ml_relief.get("model")],
    }

    # -----------------------------------------------------------------------
    # Layer 2: RULE-BASED CALCULATION
    # -----------------------------------------------------------------------
    target_lat = float(incident_data.get("latitude", origin_lat or 12.9716))
    target_lon = float(incident_data.get("longitude", origin_lon or 77.5946))

    # Nearest hospital calculation
    hospitals = db.query(Hospital).filter(Hospital.is_deleted == False).all()
    nearest_hospital = None
    min_hosp_dist = float("inf")
    for hosp in hospitals:
        dist = haversine_distance_km(target_lat, target_lon, hosp.latitude, hosp.longitude)
        if dist < min_hosp_dist:
            min_hosp_dist = dist
            nearest_hospital = {
                "id": str(hosp.id),
                "name": getattr(hosp, "hospital_name", getattr(hosp, "name", "Hospital")),
                "distance_km": dist,
                "icu_available": getattr(hosp, "icu_beds", getattr(hosp, "available_beds", 10)),
                "emergency_status": "OPERATIONAL",
            }

    # Nearest shelter calculation
    shelters = db.query(Shelter).filter(Shelter.is_deleted == False).all()
    nearest_shelter = None
    min_shelt_dist = float("inf")
    for shelt in shelters:
        dist = haversine_distance_km(target_lat, target_lon, shelt.latitude, shelt.longitude)
        if dist < min_shelt_dist:
            min_shelt_dist = dist
            nearest_shelter = {
                "id": str(shelt.id),
                "name": getattr(shelt, "shelter_name", getattr(shelt, "name", "Shelter")),
                "distance_km": dist,
                "available_capacity": getattr(shelt, "current_occupancy", getattr(shelt, "capacity", 100)),
            }

    # Resource stock match
    available_resources = db.query(Resource).filter(Resource.is_deleted == False).all()
    resource_summary = [
        {
            "id": str(r.id),
            "name": getattr(r, "resource_type", getattr(r, "name", "Resource")),
            "category": getattr(r, "resource_type", "General"),
            "available_quantity": getattr(r, "available_quantity", getattr(r, "quantity", 100)),
            "status": getattr(r, "status", "AVAILABLE"),
        }
        for r in available_resources[:5]
    ]

    rule_based_output = {
        "layer_type": "RULE-BASED CALCULATION",
        "affected_population": incident_data.get("population_affected", 0),
        "households_affected": incident_data.get("households_affected", 0),
        "nearest_suitable_hospital": nearest_hospital,
        "nearest_suitable_shelter": nearest_shelter,
        "allocated_resource_stock": resource_summary,
        "recommended_actions": [
            f"Dispatch {ml_relief.get('recommended_relief_units')} relief units immediately.",
            f"Set operational priority to {ml_priority.get('allocation_priority')}.",
            "Coordinate emergency triage with nearest hospital.",
            "Establish secondary relief staging area at shelter location.",
        ],
    }

    # -----------------------------------------------------------------------
    # Layer 3: ROUTING RESULT
    # -----------------------------------------------------------------------
    start_lat = origin_lat if origin_lat is not None else target_lat - 0.05
    start_lon = origin_lon if origin_lon is not None else target_lon - 0.05

    routing_res = calculate_emergency_route(
        origin_lat=start_lat,
        origin_lon=start_lon,
        dest_lat=target_lat,
        dest_lon=target_lon,
        vehicle_type="rescue_truck",
        db=db,
    )

    routing_output = {
        "layer_type": "ROUTING RESULT",
        "route_status": routing_res.get("status"),
        "is_rerouted": routing_res.get("is_rerouted", False),
        "distance_km": routing_res.get("distance_km") or routing_res.get("alternate_route", {}).get("distance_km"),
        "eta_minutes": routing_res.get("eta_minutes") or routing_res.get("alternate_route", {}).get("eta_minutes"),
        "blocked_segment": routing_res.get("blocked_segment"),
        "reroute_reason": routing_res.get("reroute_reason"),
        "provider": routing_res.get("provider"),
    }

    return {
        "action_plan_id": f"AP-{incident_data.get('population_affected', 1000)}",
        "ml_prediction": ml_output,
        "rule_based_calculation": rule_based_output,
        "routing_result": routing_output,
    }
