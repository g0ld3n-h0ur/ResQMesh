"""
tests/test_domain_modules.py

Integration tests for core domain endpoints (Auth, Disasters, Reports, Resources, Hospitals, Shelters, Volunteer, Dashboard).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    email = "gov.admin@tn.gov.in"
    password = "SecurePassword123!"

    login_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    if login_res.status_code == 200:
        token = login_res.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    import time
    unique_email = f"officer.{int(time.time())}@disaster.gov.in"
    reg_payload = {
        "full_name": "Domain Test Officer",
        "email": unique_email,
        "phone": f"+9198{int(time.time()) % 100000000:08d}",
        "password": password,
        "organization_name": "State Response Force",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
    }
    client.post("/api/v1/auth/register/government", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", data={"username": unique_email, "password": password})
    if login_res.status_code == 200:
        token = login_res.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}


def test_auth_register_and_login(auth_headers):
    assert "Authorization" in auth_headers

    # Test GET /auth/me
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["success"] is True


def test_disasters_list():
    response = client.get("/api/v1/disasters")
    assert response.status_code in [200, 307]


def test_reports_list(auth_headers):
    response = client.get("/api/v1/reports/", headers=auth_headers)
    assert response.status_code == 200


def test_resources_list(auth_headers):
    response = client.get("/api/v1/resources/", headers=auth_headers)
    assert response.status_code == 200


def test_hospitals_list(auth_headers):
    response = client.get("/api/v1/hospitals/", headers=auth_headers)
    assert response.status_code == 200


def test_shelters_list(auth_headers):
    response = client.get("/api/v1/shelters/", headers=auth_headers)
    assert response.status_code == 200


def test_dashboard_summary(auth_headers):
    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
