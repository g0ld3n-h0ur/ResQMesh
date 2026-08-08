"""
tests/test_domain_modules.py

Integration tests for core domain endpoints (Auth, Disasters, Reports, Resources, Hospitals, Shelters, Volunteer, Dashboard).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_token():
    email = "officer.domain@disaster.gov.in"
    password = "SecurePassword123!"

    # Register government user
    reg_payload = {
        "full_name": "Domain Test Officer",
        "email": email,
        "phone": "+919876543210",
        "password": password,
        "organization_name": "State Response Force",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
    }
    client.post("/api/v1/auth/register/government", json=reg_payload)

    # Login
    login_payload = {
        "username": email,
        "password": password,
    }
    login_res = client.post("/api/v1/auth/login", data=login_payload)
    if login_res.status_code == 200:
        return login_res.json().get("access_token")
    return None


def test_auth_register_and_login():
    token = get_auth_token()
    assert token is not None

    # Test GET /auth/me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["success"] is True


def test_disasters_list():
    response = client.get("/api/v1/disasters")
    assert response.status_code in [200, 307]


def test_reports_list():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/api/v1/reports/", headers=headers)
    assert response.status_code == 200


def test_resources_list():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/api/v1/resources/", headers=headers)
    assert response.status_code == 200


def test_hospitals_list():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/api/v1/hospitals/", headers=headers)
    assert response.status_code == 200


def test_shelters_list():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/api/v1/shelters/", headers=headers)
    assert response.status_code == 200


def test_dashboard_summary():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert response.status_code == 200
