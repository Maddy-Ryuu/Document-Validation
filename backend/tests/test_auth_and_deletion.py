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
from app.models.models import Application, Institution, AuditEvent, User, InstitutionReferenceRecord
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


def test_06_unauthenticated_institution_deletion_rejected():
    """6. Deleting an institution without authentication header is rejected with 401."""
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-NOAUTH-{unique_id}",
        "name": f"NoAuth Institute {unique_id}",
        "institution_type": "Engineering",
        "state": "Delhi",
        "city": "New Delhi",
    })
    inst_id = inst_res.json()["id"]

    del_res = client.delete(f"/api/institutions/{inst_id}")
    assert del_res.status_code == 401
    assert "Authentication required" in del_res.json()["detail"]


def test_07_non_admin_officer_cannot_delete_institution():
    """7. Scrutiny officers or reviewers without admin privileges are rejected with 403."""
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-FORBID-{unique_id}",
        "name": f"Forbidden Role Institute {unique_id}",
        "institution_type": "Management",
        "state": "Karnataka",
        "city": "Bengaluru",
    })
    inst_id = inst_res.json()["id"]

    # Login as compliance officer (non-admin)
    login_res = client.post("/api/auth/login", json={
        "email": "officer@aicte.gov.in",
        "password": "aicte2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    del_res = client.delete(f"/api/institutions/{inst_id}", headers=headers)
    assert del_res.status_code == 403
    assert "Administrative privilege required" in del_res.json()["detail"]


def test_08_nonexistent_institution_deletion_returns_404():
    """8. Administrator attempting to delete nonexistent institution receives 404."""
    login_res = client.post("/api/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "admin2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    del_res = client.delete("/api/institutions/nonexistent-inst-id-99999", headers=headers)
    assert del_res.status_code == 404
    assert "Institution not found" in del_res.json()["detail"]


def test_09_institution_with_linked_applications_prohibits_deletion():
    """9. Institution with linked active applications returns 409 Conflict and preserves records."""
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-CONFLICT-{unique_id}",
        "name": f"Active Apps Institute {unique_id}",
        "institution_type": "Pharmacy",
        "state": "Tamil Nadu",
        "city": "Chennai",
    })
    inst_id = inst_res.json()["id"]

    # Link an application
    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
    })
    assert app_res.status_code == 201

    # Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "admin2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt deletion
    del_res = client.delete(f"/api/institutions/{inst_id}", headers=headers)
    assert del_res.status_code == 409
    assert "Cannot delete institution" in del_res.json()["detail"]
    assert "active application" in del_res.json()["detail"]

    # Verify institution still exists
    get_res = client.get("/api/institutions")
    inst_ids = [item["id"] for item in get_res.json()["items"]]
    assert inst_id in inst_ids


def test_10_authoritative_reference_record_cannot_be_deleted():
    """10. Attempting to delete an authoritative reference record is rejected and record is protected."""
    db = get_test_db()
    ref_id = str(uuid.uuid4())
    try:
        ref_record = InstitutionReferenceRecord(
            id=ref_id,
            aicte_permanent_id=f"PERM-TEST-{uuid.uuid4().hex[:6].upper()}",
            legal_name="Authoritative Central Reference Institute",
            institution_type="Engineering",
            state="Maharashtra",
            district_or_city="Pune",
            normalized_name="authoritative central reference institute",
            normalized_city="pune",
            normalized_state="maharashtra",
            verification_status="OFFICIAL_VERIFIED",
            source_provenance="AICTE Official Registry",
            is_official=True,
        )
        db.add(ref_record)
        db.commit()
    finally:
        db.close()

    # Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "admin2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Deletion should be rejected
    del_res = client.delete(f"/api/institutions/{ref_id}", headers=headers)
    assert del_res.status_code == 403
    assert "Authoritative regulatory reference records cannot be deleted" in del_res.json()["detail"]

    # Verify reference record remains completely intact
    db = get_test_db()
    try:
        persisted = db.query(InstitutionReferenceRecord).filter(InstitutionReferenceRecord.id == ref_id).first()
        assert persisted is not None
        assert persisted.legal_name == "Authoritative Central Reference Institute"
    finally:
        db.close()


def test_11_admin_authorized_institution_deletion_succeeds_and_preserves_audit():
    """11. Admin deletes eligible institution (0 linked apps); institution is deleted & audit event is preserved."""
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-CLEAN-{unique_id}",
        "name": f"Clean Delete Institute {unique_id}",
        "institution_type": "Engineering",
        "state": "Gujarat",
        "city": "Ahmedabad",
    })
    assert inst_res.status_code == 201
    inst_id = inst_res.json()["id"]

    # Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": "admin@aicte.gov.in",
        "password": "admin2026!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete institution
    del_res = client.delete(f"/api/institutions/{inst_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
    assert del_res.json()["deleted_institution_id"] == inst_id

    # Verify institution is gone from institutions query
    db = get_test_db()
    try:
        deleted_inst = db.query(Institution).filter(Institution.id == inst_id).first()
        assert deleted_inst is None

        # Verify audit event is preserved
        audit = db.query(AuditEvent).filter(
            AuditEvent.entity_id == inst_id,
            AuditEvent.action == "INSTITUTION_DELETE",
        ).first()
        assert audit is not None
        assert audit.details["authorized_by"] == "admin@aicte.gov.in"
        assert audit.details["authorized_role"] == "admin"
        assert audit.details["retention_policy"] == "FORENSIC_AUDIT_LOG_PRESERVED"
    finally:
        db.close()
