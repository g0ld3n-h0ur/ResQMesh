"""
tests/test_ml_pipeline.py

Integration tests for the ML pipeline trained on disaster_relief_resource_allocation.csv.
"""

import pytest
from ml.predict import predict_allocation_priority, predict_relief_units


def test_ml_priority_prediction():
    sample = {
        "disaster_type": "Flood",
        "severity_level": "High",
        "population_affected": 5000,
        "households_affected": 1200,
        "infrastructure_damage_score": 50.0,
        "accessibility_status": "Accessible",
        "nearest_relief_center_distance_km": 10.0,
        "available_volunteers": 30,
        "medical_teams_available": 3,
        "food_stock_kg": 500.0,
        "water_stock_liters": 2000.0,
        "shelter_capacity": 300.0,
        "funding_available_usd": 25000.0,
        "vulnerability_index": 0.5,
        "ngo_present": True,
        "government_response_active": True,
        "communication_status": "Full",
        "power_status": "Partial",
    }

    result = predict_allocation_priority(sample)
    assert "allocation_priority" in result
    assert result["allocation_priority"] in ["Low", "Medium", "High", "Critical"]
    assert "confidence" in result
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["model"] == "priority_classifier"


def test_ml_relief_units_prediction():
    sample = {
        "disaster_type": "Flood",
        "severity_level": "High",
        "population_affected": 5000,
        "households_affected": 1200,
        "infrastructure_damage_score": 50.0,
        "accessibility_status": "Accessible",
        "nearest_relief_center_distance_km": 10.0,
        "available_volunteers": 30,
        "medical_teams_available": 3,
        "food_stock_kg": 500.0,
        "water_stock_liters": 2000.0,
        "shelter_capacity": 300.0,
        "funding_available_usd": 25000.0,
        "vulnerability_index": 0.5,
        "ngo_present": True,
        "government_response_active": True,
        "communication_status": "Full",
        "power_status": "Partial",
    }

    result = predict_relief_units(sample)
    assert "recommended_relief_units" in result
    assert isinstance(result["recommended_relief_units"], int)
    assert result["recommended_relief_units"] >= 0
    assert result["model"] == "relief_units_regressor"
