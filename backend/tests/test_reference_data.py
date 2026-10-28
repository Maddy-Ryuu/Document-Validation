"""
Tests for Phase 2 Authoritative Reference Data & Cross-Verification Layer.
Verifies:
1. Seed idempotency and synthetic benchmark provenance labeling.
2. Synthetic benchmarks rejected as proof of official statutory verification (routes to MANUAL_SCRUTINY_REQUIRED).
3. Exact match against an eligible officially verified test fixture (produces AUTO_VERIFIED).
4. Mismatched institution identity detection (REFERENCE_MISMATCH).
5. Missing reference records requiring manual review (REFERENCE_NOT_FOUND).
6. Programme and sanctioned-intake mismatch for intake increase (PROGRAMME_INTAKE_MISMATCH).
7. Outdated approval history continuity gaps (OUTDATED_APPROVAL).
8. Unauthorized quota applications flagged (UNAPPROVED_QUOTA).
9. Authorized quota applications confirmed.
10. Audit event recorded on every comparison.
11. Reference data REST APIs.
"""
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db, Base
from app.services.reference_data import ReferenceDataService, OFFICIAL_SOURCE, DEMO_SOURCE
from app.models.models import (
    InstitutionReferenceRecord,
    ApprovedProgrammeReference,
    InstitutionApprovalHistory,
    AuditEvent,
)

# In-memory test database
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
    yield
    app.dependency_overrides.pop(get_db, None)


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
# 1. SEED IDEMPOTENCY & SYNTHETIC PROVENANCE
# ===========================================================================

def test_01_seed_idempotency_and_synthetic_provenance():
    """1. Confirms benchmarks are seeded, labeled synthetic, and seeding is idempotent without duplicates."""
    db = TestingSessionLocal()
    try:
        refs = db.query(InstitutionReferenceRecord).all()
        assert len(refs) >= 4

        # Verify all seeded benchmark institutions are explicitly synthetic
        for r in refs:
            assert r.is_official is False, f"Seeded benchmark {r.aicte_permanent_id} must have is_official=False"
            assert r.verification_status == "SYNTHETIC_BENCHMARK"
            assert "Synthetic Demonstration Benchmark" in r.source_provenance

        inst1 = db.query(InstitutionReferenceRecord).filter_by(aicte_permanent_id="AICTE-INST-001").first()
        assert inst1 is not None
        assert len(inst1.approved_programmes) == 2
        assert len(inst1.approval_history) == 3

        # Test idempotency: re-running seed does not duplicate records
        count_before = db.query(InstitutionReferenceRecord).count()
        count_after = ReferenceDataService.seed_authoritative_benchmarks(db)
        assert count_before == count_after
    finally:
        db.close()


# ===========================================================================
# 2. SYNTHETIC REFERENCE REJECTED AS PROOF OF OFFICIAL VERIFICATION
# ===========================================================================

def test_02_synthetic_reference_rejected_as_official_verification():
    """2. Submitting an application matching a synthetic benchmark routes to MANUAL_SCRUTINY_REQUIRED, never AUTO_VERIFIED."""
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
        assert report["is_official"] is False
        assert report["verification_status"] == "SYNTHETIC_BENCHMARK"
        assert report["recommendation"] == "MANUAL_SCRUTINY_REQUIRED"

        # Explicit synthetic warning finding present
        synth_f = next((f for f in report["findings"] if f["finding_type"] == "SYNTHETIC_REFERENCE_BENCHMARK"), None)
        assert synth_f is not None
        assert synth_f["severity"] == "WARNING"
        assert "synthetic demonstration benchmark" in synth_f["message"].lower()
    finally:
        db.close()


# ===========================================================================
# 3. EXACT MATCH AGAINST AN ELIGIBLE OFFICIALLY VERIFIED TEST FIXTURE
# ===========================================================================

def test_03_exact_match_against_eligible_officially_verified_test_fixture():
    """3. An eligible officially verified fixture (is_official=True, OFFICIAL_VERIFIED) produces AUTO_VERIFIED."""
    db = TestingSessionLocal()
    try:
        # Create an official statutory reference fixture
        official_ref = InstitutionReferenceRecord(
            aicte_permanent_id="AICTE-OFFICIAL-099",
            legal_name="National Institute of Technical Excellence",
            institution_type="Engineering",
            state="Delhi",
            district_or_city="New Delhi",
            address="Vasant Kunj Institutional Area, New Delhi 110070",
            standing_status="Approved",
            established_year=2000,
            initial_approval_year=2001,
            latest_approval_year=2025,
            verification_status="OFFICIAL_VERIFIED",
            source_provenance=OFFICIAL_SOURCE,
            source_document_ref="AICTE/NRC/1-99887766/2025/EOA",
            data_freshness_date=datetime(2026, 3, 31),
            is_official=True,
        )
        db.add(official_ref)
        db.flush()

        # Add continuous 2025-2026 approval history
        hist = InstitutionApprovalHistory(
            institution_reference_id=official_ref.id,
            academic_year="2025-2026",
            eoa_application_number="AICTE/NRC/1-99887766/2025/EOA",
            eoa_issue_date=datetime(2025, 5, 20),
            effective_start_date=datetime(2025, 7, 1),
            effective_end_date=datetime(2026, 6, 30),
            total_sanctioned_intake=240,
            approval_type="Extension of Approval",
            issuing_authority="Member Secretary, AICTE",
            is_latest=True,
        )
        db.add(hist)
        db.commit()

        # Submit matching application
        app_id, _ = create_app_helper(
            identifier="AICTE-OFFICIAL-099",
            name="National Institute of Technical Excellence",
            state="Delhi",
            city="New Delhi",
        )

        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True
        assert report["is_official"] is True
        assert report["verification_status"] == "OFFICIAL_VERIFIED"
        assert report["recommendation"] == "AUTO_VERIFIED"
        assert report["matched_fields"]["name"]["match"] is True

        # Confirms official approval verified finding
        verified_f = next(f for f in report["findings"] if f["finding_type"] == "REFERENCE_VERIFIED")
        assert "Continuous approval verified" in verified_f["message"]
    finally:
        db.close()


# ===========================================================================
# 4. MISMATCHED INSTITUTION IDENTITY
# ===========================================================================

def test_04_mismatched_institution_identity():
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
# 5. MISSING REFERENCE REQUIRING MANUAL REVIEW
# ===========================================================================

def test_05_missing_reference_requiring_manual_review():
    """5. An unknown institution ID returns UNRESOLVED_MANUAL_REVIEW without fabricating fake approvals."""
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

        not_found_f = next(f for f in report["findings"] if f["finding_type"] == "REFERENCE_NOT_FOUND")
        assert "No official AICTE reference ledger record found" in not_found_f["message"]
        assert not_found_f["severity"] == "WARNING"
    finally:
        db.close()


# ===========================================================================
# 6. PROGRAMME OR SANCTIONED INTAKE MISMATCH
# ===========================================================================

def test_06_programme_or_sanctioned_intake_mismatch():
    """6. Increase in Intake application flags PROGRAMME_INTAKE_MISMATCH if programmes lack NBA accreditation or are missing."""
    db = TestingSessionLocal()
    try:
        # Create reference institution with non-accredited programmes
        non_nba_ref = InstitutionReferenceRecord(
            aicte_permanent_id="AICTE-NON-NBA-001",
            legal_name="Eastern Technical Polytechnic",
            institution_type="Engineering",
            state="West Bengal",
            district_or_city="Kolkata",
            standing_status="Approved",
            verification_status="SYNTHETIC_BENCHMARK",
            source_provenance=DEMO_SOURCE,
            is_official=False,
            data_freshness_date=datetime(2026, 3, 31),
        )
        db.add(non_nba_ref)
        db.flush()

        p = ApprovedProgrammeReference(
            institution_reference_id=non_nba_ref.id,
            programme_name="Engineering",
            course_name="Civil Engineering",
            level="UG",
            approved_intake=60,
            nri_quota_approved=False,
            pio_fn_quota_approved=False,
            accreditation_status="Non-Accredited",
            academic_year="2025-2026",
            is_active=True,
        )
        db.add(p)

        hist = InstitutionApprovalHistory(
            institution_reference_id=non_nba_ref.id,
            academic_year="2025-2026",
            effective_start_date=datetime(2025, 7, 1),
            effective_end_date=datetime(2026, 6, 30),
            total_sanctioned_intake=60,
            approval_type="Extension of Approval",
            issuing_authority="AICTE",
            is_latest=True,
        )
        db.add(hist)
        db.commit()

        # Submit Increase in Intake application
        app_id, _ = create_app_helper(
            identifier="AICTE-NON-NBA-001",
            name="Eastern Technical Polytechnic",
            state="West Bengal",
            city="Kolkata",
            category="Increase in Intake",
        )

        report = ReferenceDataService.match_application_against_reference(db, app_id)
        assert report["reference_matched"] is True

        intake_f = next(f for f in report["findings"] if f["finding_type"] == "PROGRAMME_INTAKE_MISMATCH")
        assert "mandate valid NBA accreditation for intake expansion" in intake_f["message"]
        assert intake_f["severity"] == "WARNING"
        assert report["recommendation"] == "MANUAL_SCRUTINY_REQUIRED"
    finally:
        db.close()


# ===========================================================================
# 7. OUTDATED APPROVAL HISTORY
# ===========================================================================

def test_07_outdated_approval_history():
    """7. An institution whose latest approval was 2023-2024 is flagged for an approval gap prior to 2026-2027."""
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
        assert report["recommendation"] == "MANUAL_SCRUTINY_REQUIRED"
    finally:
        db.close()


# ===========================================================================
# 8. UNAUTHORIZED QUOTA APPLICATION FLAGGED
# ===========================================================================

def test_08_unauthorized_quota_application_flagged():
    """8. Submitting NRI Quota for an institute without approved quota seats in reference data flags UNAPPROVED_QUOTA."""
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
# 9. AUTHORIZED QUOTA APPLICATION CONFIRMED
# ===========================================================================

def test_09_authorized_quota_application_confirmed():
    """9. Submitting NRI Quota for INST-002 (which has approved quota in reference records) confirms quota approval."""
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
# 10. AUDIT EVENT RECORDED ON REFERENCE MATCH COMPARISON
# ===========================================================================

def test_10_audit_event_recorded_on_reference_match():
    """10. Triggering POST /api/applications/{id}/reference-match creates a traceable AuditEvent."""
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
        assert "recommendation" in audit.details
        assert audit.details["findings_count"] >= 1
    finally:
        db.close()


# ===========================================================================
# 11. REFERENCE DATA REST APIS
# ===========================================================================

def test_11_reference_data_rest_apis():
    """11. Verifies list, get, and match REST API endpoints."""
    # List reference institutions
    res_list = client.get("/api/reference-data/institutions")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) >= 4

    # Search by permanent ID (supports INST or DEMO alias)
    res_search = client.get("/api/reference-data/institutions?search=AICTE-INST-002")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

    # Detail view
    res_detail = client.get("/api/reference-data/institutions/AICTE-INST-001")
    assert res_detail.status_code == 200
    data = res_detail.json()
    assert data["aicte_permanent_id"] == "AICTE-INST-001"
    assert len(data["approved_programmes"]) == 2
    assert len(data["approval_history"]) == 3
    assert data["is_official"] is False
    assert data["verification_status"] == "SYNTHETIC_BENCHMARK"

    # Application reference match endpoint
    app_id, _ = create_app_helper("AICTE-INST-001", "Delhi Institute of Technology & Advanced Sciences", "Delhi", "New Delhi")
    res_match = client.get(f"/api/applications/{app_id}/reference-match")
    assert res_match.status_code == 200
    match_data = res_match.json()
    assert match_data["reference_matched"] is True
    assert match_data["verification_status"] == "SYNTHETIC_BENCHMARK"
    assert match_data["recommendation"] == "MANUAL_SCRUTINY_REQUIRED"
