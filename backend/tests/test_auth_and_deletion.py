"""
test_auth_and_deletion.py
Tests for:
1. Real backend authentication (/api/auth/login, /api/auth/me, /api/auth/logout).
2. Protection of unauthorized access.
3. Application deletion action with authorization and forensic audit preservation.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.main import app
from app.db.session import Base, get_db
from app.models.models import Application, Institution, AuditEvent, User
from app.core.auth import hash_password

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_test_db():
    if get_db in app.dependency_overrides:
        return next(app.dependency_overrides[get_db]())
    return TestingSessionLocal()


@pytest.fixture(autouse=True)
def setup_auth_test_env():
    app.dependency_overrides[get_db] = override_get_db
    yield


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


def setup_test_app_helper():
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-DEL-{unique_id}",
        "name": f"Test Institution for Deletion {unique_id}",
        "institution_type": "Engineering",
        "state": "Maharashtra",
        "city": "Mumbai",
    })
    inst_id = inst_res.json()["id"]

    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
    })
    return app_res.json()["id"]


def test_01_login_with_bootstrap_officer_credentials():
    """1. Verifies authentication using designated AICTE Scrutiny Officer credentials."""
    login_res = client.post("/api/auth/login", json={
        "email": "officer@aicte.gov.in",
        "password": "aicte2026!",
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "officer@aicte.gov.in"
    assert data["user"]["role"] == "compliance_officer"


def test_02_login_with_invalid_credentials_rejected():
    """2. Verifies that invalid passwords or unregistered emails are rejected with 401."""
    # Wrong password
    res1 = client.post("/api/auth/login", json={
        "email": "officer@aicte.gov.in",
        "password": "wrongpassword123",
    })
    assert res1.status_code == 401
    assert "Invalid official email or password" in res1.json()["detail"]

    # Unknown email
    res2 = client.post("/api/auth/login", json={
        "email": "intruder@unknown.com",
        "password": "somepassword",
    })
    assert res2.status_code == 401


def test_03_auth_me_and_logout_endpoints():
    """3. Verifies /api/auth/me returns identity and /api/auth/logout functions with bearer token."""
    login_res = client.post("/api/auth/login", json={
        "email": "reviewer@aicte.gov.in",
        "password": "reviewer2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /api/auth/me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "reviewer@aicte.gov.in"
    assert me_data["role"] == "reviewer"

    # /api/auth/logout
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert "Logged out successfully" in logout_res.json()["message"]


def test_04_unauthorized_deletion_rejected():
    """4. Deleting an application without authentication is rejected with 401."""
    app_id = setup_test_app_helper()
    del_res = client.delete(f"/api/applications/{app_id}")
    assert del_res.status_code == 401
    assert "Authentication required" in del_res.json()["detail"]


def test_05_authorized_deletion_preserves_forensic_audit():
    """5. Authorized deletion removes application record and records forensic AuditEvent."""
    app_id = setup_test_app_helper()

    # Login as officer to obtain token
    login_res = client.post("/api/auth/login", json={
        "email": "officer@aicte.gov.in",
        "password": "aicte2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete application
    del_res = client.delete(f"/api/applications/{app_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify application is no longer in applications table
    get_res = client.get(f"/api/applications/{app_id}")
    assert get_res.status_code == 404

    # Verify forensic audit event is preserved in database
    db = get_test_db()
    try:
        audit = db.query(AuditEvent).filter(
            AuditEvent.entity_id == app_id,
            AuditEvent.action == "APPLICATION_DELETE",
        ).first()
        assert audit is not None
        assert audit.details["authorized_by"] == "officer@aicte.gov.in"
        assert audit.details["retention_policy"] == "FORENSIC_AUDIT_LOG_PRESERVED"
    finally:
        db.close()
