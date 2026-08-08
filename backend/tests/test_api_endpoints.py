"""
tests/test_api_endpoints.py

Integration tests for FastAPI endpoints (Health, Prediction, Commander, Routing, Governance, CSR).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_system_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_system_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert data["status"] == "running"


def test_routing_calculation():
    payload = {
        "origin_latitude": 12.9716,
        "origin_longitude": 77.5946,
        "destination_latitude": 13.0827,
        "destination_longitude": 80.2707,
        "vehicle_type": "ambulance",
        "is_simulation": True,
    }
    response = client.post("/api/v1/routing/calculate-route", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "data" in res
    assert res["data"]["status"] in ["SAFE_ROUTE", "REROUTED"]


def test_commander_action_plan():
    payload = {
        "disaster_type": "Flood",
        "severity_level": "High",
        "population_affected": 5000,
        "households_affected": 1200,
        "infrastructure_damage_score": 50.0,
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
        "accessibility_status": "Accessible",
        "communication_status": "Full",
        "power_status": "Partial",
        "latitude": 12.9716,
        "longitude": 77.5946,
    }
    response = client.post("/api/v1/commander/action-plan", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert "ml_prediction" in data
    assert "rule_based_calculation" in data
    assert "routing_result" in data


def test_governance_audit_trail():
    response = client.get("/api/v1/governance/audit-trail")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True


def test_governance_anomalies():
    response = client.post("/api/v1/governance/anomalies/run-checks")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True


def test_governance_situation_report():
    response = client.get("/api/v1/governance/reports/executive-situation")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "report_id" in res["data"]


def test_csr_public_transparency():
    response = client.get("/api/v1/csr/transparency/public-summary")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "public_aggregated_transparency" in res["data"]
