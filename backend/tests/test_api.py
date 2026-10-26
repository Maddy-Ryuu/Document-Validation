import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Ensure all models are registered
from app.main import app
from app.db.session import Base, get_db

# Use in-memory SQLite with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in testing engine
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_dashboard_empty_initial_state():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_applications"] == 0
    assert data["in_validation"] == 0
    assert data["action_required"] == 0
    assert data["verified_documents"] == 0


def test_institution_creation_and_list():
    payload = {
        "institution_identifier": "TEST-INST-101",
        "name": "Indian Institute of Science & Technology",
        "institution_type": "Engineering",
        "state": "Karnataka",
        "city": "Bengaluru"
    }
    create_res = client.post("/api/institutions", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["institution_identifier"] == "TEST-INST-101"
    assert created_data["name"] == payload["name"]

    # Test list institutions
    list_res = client.get("/api/institutions")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(inst["institution_identifier"] == "TEST-INST-101" for inst in list_data["items"])


def test_duplicate_institution_protection():
    payload = {
        "institution_identifier": "TEST-INST-101",
        "name": "Duplicate Institute",
        "institution_type": "Management",
        "state": "Delhi",
        "city": "New Delhi"
    }
    res = client.post("/api/institutions", json=payload)
    assert res.status_code in (400, 409)
    assert "already exists" in res.json()["detail"].lower()


def test_application_creation_and_kpi_update():
    # First get institution ID
    inst_res = client.get("/api/institutions")
    inst_id = inst_res.json()["items"][0]["id"]

    # Create application
    app_payload = {
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
    }
    app_res = client.post("/api/applications", json=app_payload)
    assert app_res.status_code == 201
    created_app = app_res.json()
    assert created_app["status"] == "Under Validation"
    assert created_app["application_category"] == "Extension of Approval (EoA)"
    assert created_app["institution_id"] == inst_id

    # Verify KPI updated in summary
    summary_res = client.get("/api/dashboard/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["total_applications"] >= 1
    assert summary_data["in_validation"] >= 1

    # Verify Detail API
    detail_res = client.get(f"/api/applications/{created_app['id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == created_app["id"]

    # Verify Update API
    patch_res = client.patch(f"/api/applications/{created_app['id']}", json={"status": "Verified"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Verified"


def test_invalid_application_creation():
    # Non-existent institution id
    app_payload = {
        "institution_id": "non-existent-uuid",
        "application_category": "New Institute",
        "academic_year": "2026-2027",
    }
    res = client.post("/api/applications", json=app_payload)
    assert res.status_code == 400
    assert "not found" in res.json()["detail"]
