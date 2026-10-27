import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def setup_sidebar_data():
    uid = uuid.uuid4().hex[:6].upper()
    # 1. Create institution via client
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-SB-{uid}",
        "name": f"Sidebar Test Institute {uid}",
        "institution_type": "Engineering",
        "city": "Pune",
        "state": "Maharashtra",
    })
    assert inst_res.status_code == 201
    inst_id = inst_res.json()["id"]

    # 2. Create application via client
    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
    })
    assert app_res.status_code == 201
    app_data = app_res.json()

    return {
        "institution_id": inst_id,
        "application_id": app_data["id"],
        "application_identifier": app_data["application_identifier"],
    }


def test_list_all_documents(setup_sidebar_data):
    res = client.get("/api/documents")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_review_document(setup_sidebar_data):
    # Try review on a non-existent doc -> 404
    fake_id = str(uuid.uuid4())
    res404 = client.post(f"/api/documents/{fake_id}/review?action=Needs Review")
    assert res404.status_code == 404

    # Invalid action -> 400
    bad_res = client.post(f"/api/documents/{fake_id}/review?action=InvalidAction")
    assert bad_res.status_code == 400


def test_review_queue(setup_sidebar_data):
    res = client.get("/api/queue")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_audit_events():
    res = client.get("/api/audit-events")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_analytics_reports():
    res = client.get("/api/reports/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_applications" in data
    assert "status_breakdown" in data
    assert "risk_breakdown" in data
    assert "category_breakdown" in data


def test_system_settings():
    res = client.get("/api/settings/system")
    assert res.status_code == 200
    data = res.json()
    assert "system" in data
    assert "officer_profile" in data
    assert "security_status" in data
    assert data["system"]["handbook_edition"] == "APH 2026-2027"
    assert data["officer_profile"]["role"] == "Scrutiny Officer / Reviewer"
