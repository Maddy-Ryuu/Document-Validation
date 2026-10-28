import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

import app.models
from app.main import app
from app.db.session import Base, get_db
from app.models.models import (
    Application,
    Institution,
    AuditEvent,
    InstitutionReferenceRecord,
    ApprovedProgrammeReference,
    InstitutionApprovalHistory,
)
from app.services.reference_data import ReferenceDataService

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


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def init_benchmarks():
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    try:
        ReferenceDataService.seed_authoritative_benchmarks(db)
    finally:
        db.close()


def create_app_helper(identifier: str, name: str, state: str, city: str, category: str = "Extension of Approval (EoA)"):
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": identifier,
        "name": name,
        "institution_type": "Engineering",
        "state": state,
        "city": city,
    })
    if inst_res.status_code == 409:
        search_res = client.get(f"/api/institutions?search={identifier}")
        inst_id = search_res.json()["items"][0]["id"]
        client.patch(f"/api/institutions/{inst_id}", json={
            "name": name,
            "state": state,
            "city": city,
        })
    else:
        assert inst_res.status_code == 201
        inst_id = inst_res.json()["id"]

    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": category,
        "academic_year": "2026-2027",
    })
    assert app_res.status_code == 201
    return app_res.json()["id"], inst_id


# ===========================================================================
# 1. SEEDING & PROVENANCE
# ===========================================================================

def test_01_seed_authoritative_reference_benchmarks():
    """1. Verifies that authoritative reference benchmarks are seeded with provenance and freshness."""
    db = TestingSessionLocal()
    try:
        refs = db.query(InstitutionReferenceRecord).all()
        assert len(refs) >= 4

        inst1 = db.query(InstitutionReferenceRecord).filter_by(aicte_permanent_id="AICTE-INST-001").first()
        assert inst1 is not None
        assert inst1.verification_status == "OFFICIAL_VERIFIED"
        assert inst1.is_official is True
        assert "AICTE Central Regulatory Registry" in inst1.source_provenance
        assert inst1.data_freshness_date is not None

        # Verify linked programmes
        assert len(inst1.approved_programmes) == 2
        cse = next(p for p in inst1.approved_programmes if "Computer Science" in p.course_name)
        assert cse.approved_intake == 180
        assert cse.accreditation_status == "NBA Accredited"

        # Verify linked approval history
        assert len(inst1.approval_history) == 3
        latest = next(h for h in inst1.approval_history if h.is_latest)
        assert latest.academic_year == "2025-2026"
        assert latest.total_sanctioned_intake == 300
    finally:
        db.close()


# ===========================================================================
# 2. EXACT REFERENCE MATCHING (AUTO-VERIFIED)
# ===========================================================================

def test_02_exact_reference_match_verified():
    """2. Submitting an application matching official permanent ID and name produces AUTO_VERIFIED."""
    app_id, _ = create_app_helper(
        identifier="AICTE-INST-001",
        name="Delhi Institute of Technology & Advanced Sciences",
        state="Delhi",
        city="New Delhi",
    )

    db = TestingSessionLocal()
    try:
        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True
        assert report["aicte_permanent_id"] == "AICTE-INST-001"
        assert report["verification_status"] == "OFFICIAL_VERIFIED"
        assert report["recommendation"] == "AUTO_VERIFIED"
        assert report["is_official"] is True
        assert "AICTE Central Regulatory Registry" in report["source_provenance"]

        # Check matched fields
        assert report["matched_fields"]["name"]["match"] is True
        assert report["matched_fields"]["city"]["match"] is True
        assert report["matched_fields"]["state"]["match"] is True

        # Check approval continuity finding
        continuity_f = next((f for f in report["findings"] if f["finding_type"] == "REFERENCE_VERIFIED"), None)
        assert continuity_f is not None
        assert "Continuous approval verified" in continuity_f["message"]
    finally:
        db.close()


# ===========================================================================
# 3. MISSING REFERENCE RECORD (UNRESOLVED / MANUAL REVIEW)
# ===========================================================================

def test_03_unresolved_manual_review_when_reference_missing():
    """3. An unknown institution ID returns UNRESOLVED_MANUAL_REVIEW without fabricating fake approvals."""
    uid = uuid.uuid4().hex[:6].upper()
    app_id, _ = create_app_helper(
        identifier=f"UNKNOWN-INST-{uid}",
        name=f"Fictional University of Nowhere {uid}",
        state="Haryana",
        city="Gurugram",
    )

    db = TestingSessionLocal()
    try:
        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is False
        assert report["verification_status"] == "UNRESOLVED_MANUAL_REVIEW"
        assert report["recommendation"] == "MANUAL_SCRUTINY_REQUIRED"
        assert report["is_official"] is False
        assert len(report["findings"]) > 0

        not_found_f = next(f for f in report["findings"] if f["finding_type"] == "REFERENCE_NOT_FOUND")
        assert "No official AICTE reference ledger record found" in not_found_f["message"]
        assert "manual officer scrutiny required" in not_found_f["message"]
    finally:
        db.close()


# ===========================================================================
# 4. LEGAL NAME MISMATCH
# ===========================================================================

def test_04_identity_and_name_mismatch_detected():
    """4. If submitted institute name differs from official registered name, detects REFERENCE_MISMATCH."""
    app_id, _ = create_app_helper(
        identifier="AICTE-INST-001",
        name="Conflicting Commercial Name Institute",
        state="Delhi",
        city="New Delhi",
    )

    db = TestingSessionLocal()
    try:
        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True
        assert report["matched_fields"]["name"]["match"] is False
        assert report["recommendation"] == "REJECT_UNAUTHORIZED"

        mismatch_f = next(f for f in report["findings"] if f["finding_type"] == "REFERENCE_MISMATCH")
        assert "does not match official registered legal name" in mismatch_f["message"]
        assert mismatch_f["severity"] == "CRITICAL"
    finally:
        db.close()


# ===========================================================================
# 5. OUTDATED APPROVAL GAP DETECTED
# ===========================================================================

def test_05_outdated_approval_gap_detected():
    """5. An institution whose latest approval was 2023-2024 is flagged for an approval gap prior to 2026-2027."""
    app_id, _ = create_app_helper(
        identifier="AICTE-INST-OUTDATED",
        name="Heritage Polytechnic and Vocational College",
        state="Uttar Pradesh",
        city="Lucknow",
    )

    db = TestingSessionLocal()
    try:
        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True

        gap_f = next(f for f in report["findings"] if f["finding_type"] == "OUTDATED_APPROVAL")
        assert "Latest official approval on record is for AY 2023-2024" in gap_f["message"]
        assert "Approval gap detected" in gap_f["message"]
        assert gap_f["severity"] == "WARNING"
    finally:
        db.close()


# ===========================================================================
# 6. UNAPPROVED QUOTA APPLICATION FLAGGED
# ===========================================================================

def test_06_unapproved_quota_application_flagged():
    """6. Submitting NRI Quota for an institute without approved quota seats in reference data flags UNAPPROVED_QUOTA."""
    # INST-001 has no NRI quota approved
    app_id, _ = create_app_helper(
        identifier="AICTE-INST-001",
        name="Delhi Institute of Technology & Advanced Sciences",
        state="Delhi",
        city="New Delhi",
        category="NRI / Foreign National Quota",
    )

    db = TestingSessionLocal()
    try:
        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True

        quota_f = next(f for f in report["findings"] if f["finding_type"] == "UNAPPROVED_QUOTA")
        assert "no existing approved quota allocation" in quota_f["message"]
        assert quota_f["severity"] == "CRITICAL"
        assert report["recommendation"] == "REJECT_UNAUTHORIZED"
    finally:
        db.close()


# ===========================================================================
# 7. APPROVED QUOTA APPLICATION VERIFIED
# ===========================================================================

def test_07_approved_quota_application_verified():
    """7. Submitting NRI Quota for INST-002 (which has approved quota in reference records) is confirmed."""
    app_id, _ = create_app_helper(
        identifier="AICTE-INST-002",
        name="Maharashtra Institute of Technology & Research",
        state="Maharashtra",
        city="Pune",
        category="NRI / Foreign National Quota",
    )

    db = TestingSessionLocal()
    try:
        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True

        quota_v = next(f for f in report["findings"] if "NRI / PIO / FN quota seats" in f["message"])
        assert quota_v["finding_type"] == "REFERENCE_VERIFIED"
        assert quota_v["severity"] == "INFO"
    finally:
        db.close()


# ===========================================================================
# 8. REFERENCE DATA REST APIS
# ===========================================================================

def test_08_reference_data_rest_apis():
    """8. Verifies list, get, and match REST API endpoints."""
    # List reference institutions
    res_list = client.get("/api/reference-data/institutions")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) >= 4

    # Search by permanent ID
    res_search = client.get("/api/reference-data/institutions?search=AICTE-INST-002")
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["aicte_permanent_id"] == "AICTE-INST-002"

    # Detail view
    res_detail = client.get("/api/reference-data/institutions/AICTE-INST-001")
    assert res_detail.status_code == 200
    data = res_detail.json()
    assert data["aicte_permanent_id"] == "AICTE-INST-001"
    assert len(data["approved_programmes"]) == 2
    assert len(data["approval_history"]) == 3

    # Application reference match endpoint
    app_id, _ = create_app_helper("AICTE-INST-001", "Delhi Institute of Technology & Advanced Sciences", "Delhi", "New Delhi")
    res_match = client.get(f"/api/applications/{app_id}/reference-match")
    assert res_match.status_code == 200
    match_data = res_match.json()
    assert match_data["reference_matched"] is True
    assert match_data["verification_status"] == "OFFICIAL_VERIFIED"


# ===========================================================================
# 9. AUDIT TRAIL LOGGED ON REFERENCE MATCH
# ===========================================================================

def test_09_audit_trail_recorded_on_reference_match():
    """9. Triggering POST /api/applications/{id}/reference-match creates a traceable AuditEvent."""
    app_id, _ = create_app_helper("AICTE-INST-001", "Delhi Institute of Technology & Advanced Sciences", "Delhi", "New Delhi")
    res_trigger = client.post(f"/api/applications/{app_id}/reference-match")
    assert res_trigger.status_code == 200

    db = TestingSessionLocal()
    try:
        audit = db.query(AuditEvent).filter(
            AuditEvent.entity_id == app_id,
            AuditEvent.action == "REFERENCE_MATCH_AUDIT",
        ).first()
        assert audit is not None
        assert audit.details["reference_matched"] is True
        assert audit.details["verification_status"] == "OFFICIAL_VERIFIED"
    finally:
        db.close()
