"""
app/services/preparedness_service.py

Disaster Preparedness Simulator.
Uses actual dataset-supported ML model + deterministic calculations + current inventory state.
Does NOT train another ML model.
"""

from __future__ import annotations

from typing import Any, Dict
from sqlalchemy.orm import Session

from ml.predict import predict_allocation_priority, predict_relief_units
from app.models.resource import Resource
from app.models.shelter import Shelter


def run_preparedness_simulation(scenario_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Run a scenario simulation for disaster preparedness."""
    # Step 1: Run ML prediction for estimated demand
    ml_priority = predict_allocation_priority(scenario_data)
    ml_relief = predict_relief_units(scenario_data)

    rec_units = ml_relief.get("recommended_relief_units", 1000)
    pop = scenario_data.get("population_affected", 5000)

    # Step 2: Compare against available DB inventory
    resources = db.query(Resource).filter(Resource.is_deleted == False).all()
    avail_stock = sum(getattr(r, "quantity", 0) for r in resources)
    resource_gap = max(0, rec_units - avail_stock)

    # Step 3: Compare against available shelter capacity
    shelters = db.query(Shelter).filter(Shelter.is_deleted == False).all()
    avail_shelter = sum(getattr(s, "capacity", 0) for s in shelters)
    shelter_gap = max(0, int(pop * 0.2) - avail_shelter)

    return {
        "scenario": {
            "disaster_type": scenario_data.get("disaster_type"),
            "severity_level": scenario_data.get("severity_level"),
            "population_affected": pop,
        },
        "ml_prediction": {
            "predicted_priority": ml_priority.get("allocation_priority"),
            "predicted_relief_units": rec_units,
        },
        "scenario_estimation": {
            "available_resource_stock": avail_stock,
            "resource_gap_units": resource_gap,
            "estimated_shelter_demand": int(pop * 0.2),
            "available_shelter_capacity": avail_shelter,
            "shelter_gap": shelter_gap,
            "estimated_medical_teams_needed": max(1, int(pop / 2500)),
            "preparation_recommendations": [
                f"Procure {resource_gap} additional relief units before event peak." if resource_gap > 0 else "Inventory stock adequate for scenario.",
                f"Prepare auxiliary shelter spaces for {shelter_gap} individuals." if shelter_gap > 0 else "Shelter capacity adequate.",
                "Verify emergency communications equipment and backup power generators.",
            ],
        },
    }
