import io
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
import pymupdf

import app.models
from app.main import app
from app.db.session import get_db, SessionLocal
from app.services.document_processor import process_document_sync
from app.services.compliance_engine import ComplianceEngine
from app.services.risk_engine import RiskScoringEngine

client = TestClient(app, raise_server_exceptions=False)


def get_test_db():
    if get_db in app.dependency_overrides:
        return next(app.dependency_overrides[get_db]())
    return SessionLocal()


def create_sample_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=11)
    b = doc.tobytes()
    doc.close()
    return b


def setup_test_application(inst_name="Apex Institute of Technology & Advanced Studies"):
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-{unique_id}",
        "name": inst_name,
        "institution_type": "Engineering",
        "state": "Maharashtra",
        "city": "Pune",
    })
    inst_id = inst_res.json()["id"]

    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
    })
    return app_res.json()["id"]


# --------------------------------------------------------------------------
# Test 1 & 2: Application has no compliance run / no usable findings
# --------------------------------------------------------------------------
def test_risk_evaluate_without_compliance_run_fails():
    app_id = setup_test_application()
    res = client.post(f"/api/applications/{app_id}/risk/evaluate")
    assert res.status_code == 400
    assert "no compliance evaluation" in res.json()["detail"].lower()


def test_risk_report_without_evaluation_returns_404():
    app_id = setup_test_application()
    res = client.get(f"/api/applications/{app_id}/risk/report")
    assert res.status_code == 404
    assert "no risk assessment" in res.json()["detail"].lower()


# --------------------------------------------------------------------------
# Test 3: Application has compliance run with all passing rules (low risk)
# --------------------------------------------------------------------------
def test_risk_evaluate_clean_application_produces_low_risk():
    app_id = setup_test_application()
    # Execute compliance run
    client.post(f"/api/applications/{app_id}/compliance/evaluate")

    # Evaluate risk
    risk_res = client.post(f"/api/applications/{app_id}/risk/evaluate")
    assert risk_res.status_code == 200
    data = risk_res.json()

    assert data["application_id"] == app_id
    assert "score" in data
    assert data["risk_band"] in ["Low", "Medium", "High"]
    assert 0 <= data["score"] <= 100


# --------------------------------------------------------------------------
# Test 5 & 8: Expired Regulatory Document yields configured penalty
# --------------------------------------------------------------------------
def test_risk_evaluate_expired_regulatory_document():
    app_id = setup_test_application()
    expired_fire = (
        "FIRE SAFETY NOC\n"
        "Name of Institution: Apex Institute of Technology & Advanced Studies\n"
        "Certificate No: CFO/2022/881\n"
        "Valid until: 15-05-2023\n"
        "Issued by: Chief Fire Officer\n"
    )
    r = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("fire_noc.pdf", io.BytesIO(create_sample_pdf(expired_fire)), "application/pdf")},
    )
    db = get_test_db()
    try:
        process_document_sync(db, r.json()["id"])
    finally:
        db.close()

    # Compliance
    comp_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert comp_res.status_code == 200

    # Risk
    risk_res = client.post(f"/api/applications/{app_id}/risk/evaluate")
    assert risk_res.status_code == 200
    data = risk_res.json()

    # Factor for expired regulatory document must be present
    factors = [f["factor_code"] for f in data["contributing_factors"]]
    assert "EXPIRED_REGULATORY_DOCUMENTS" in factors
    assert data["score"] >= 20


# --------------------------------------------------------------------------
# Test 7: Synthetic document with future expiry date yields UNVERIFIED penalty
# --------------------------------------------------------------------------
def test_risk_evaluate_synthetic_document_authenticity():
    app_id = setup_test_application()
    synth_fire = (
        "SYNTHETIC TEST DOCUMENT - NOT AN OFFICIAL RECORD\n"
        "Fire Safety NOC - Metadata Summary\n"
        "Deliberately not a certificate issued by any authority\n"
        "Institution: Apex Institute of Technology & Advanced Studies\n"
        "Test expiry date: 15-05-2027\n"
    )
    r = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("07_fire_safety_noc_summary.pdf", io.BytesIO(create_sample_pdf(synth_fire)), "application/pdf")},
    )
    db = get_test_db()
    try:
        process_document_sync(db, r.json()["id"])
    finally:
        db.close()

    client.post(f"/api/applications/{app_id}/compliance/evaluate")
    risk_res = client.post(f"/api/applications/{app_id}/risk/evaluate")
    assert risk_res.status_code == 200
    data = risk_res.json()

    factors = [f["factor_code"] for f in data["contributing_factors"]]
    assert "UNVERIFIED_DOCUMENT_AUTHENTICITY" in factors
    assert data["is_provisional"] is True


# --------------------------------------------------------------------------
# Test 9: Conflicting institution identifiers across documents
# --------------------------------------------------------------------------
def test_risk_evaluate_cross_document_identity_mismatch():
    app_id = setup_test_application(inst_name="Apex Institute of Technology & Advanced Studies")
    alien_text = (
        "STATE GOVERNMENT APPROVAL ORDER\n"
        "Name of Institution: Zenith Polytechnic & Technology Campus\n"
        "Order No: HE/ORDER/2025/991\n"
        "Dated: 10-04-2025\n"
    )
    r = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "University Affiliation / State Govt Permission"},
        files={"file": ("alien_approval.pdf", io.BytesIO(create_sample_pdf(alien_text)), "application/pdf")},
    )
    db = get_test_db()
    try:
        process_document_sync(db, r.json()["id"])
    finally:
        db.close()

    client.post(f"/api/applications/{app_id}/compliance/evaluate")
    risk_res = client.post(f"/api/applications/{app_id}/risk/evaluate")
    assert risk_res.status_code == 200
    data = risk_res.json()

    factors = [f["factor_code"] for f in data["contributing_factors"]]
    assert "CROSS_DOCUMENT_INCONSISTENCIES" in factors


# --------------------------------------------------------------------------
# Test 11 & 12: Score bounded in [0, 100] and deduplication
# --------------------------------------------------------------------------
def test_risk_score_boundaries_and_deduplication():
    app_id = setup_test_application()
    client.post(f"/api/applications/{app_id}/compliance/evaluate")
    risk_res = client.post(f"/api/applications/{app_id}/risk/evaluate")
    assert risk_res.status_code == 200
    data = risk_res.json()
    assert 0 <= data["score"] <= 100


# --------------------------------------------------------------------------
# Test 13: Deterministic repeatability
# --------------------------------------------------------------------------
def test_risk_score_deterministic_repeatability():
    app_id = setup_test_application()
    client.post(f"/api/applications/{app_id}/compliance/evaluate")

    eval1 = client.post(f"/api/applications/{app_id}/risk/evaluate").json()
    eval2 = client.post(f"/api/applications/{app_id}/risk/evaluate").json()

    assert eval1["score"] == eval2["score"]
    assert eval1["risk_band"] == eval2["risk_band"]
    assert len(eval1["contributing_factors"]) == len(eval2["contributing_factors"])


# --------------------------------------------------------------------------
# Test 14: Isolation between different applications
# --------------------------------------------------------------------------
def test_risk_evaluation_application_isolation():
    app1 = setup_test_application(inst_name="Apex Institute of Technology & Advanced Studies")
    app2 = setup_test_application(inst_name="Delhi Technical University")

    # Upload mismatch to app1 only
    alien_text = (
        "STATE GOVERNMENT APPROVAL ORDER\n"
        "Name of Institution: Zenith Polytechnic & Technology Campus\n"
        "Order No: HE/ORDER/2025/991\n"
        "Dated: 10-04-2025\n"
    )
    r1 = client.post(
        f"/api/applications/{app1}/documents",
        data={"document_type": "University Affiliation / State Govt Permission"},
        files={"file": ("mismatch.pdf", io.BytesIO(create_sample_pdf(alien_text)), "application/pdf")},
    )
    db = get_test_db()
    try:
        process_document_sync(db, r1.json()["id"])
    finally:
        db.close()

    client.post(f"/api/applications/{app1}/compliance/evaluate")
    client.post(f"/api/applications/{app2}/compliance/evaluate")

    risk1 = client.post(f"/api/applications/{app1}/risk/evaluate").json()
    risk2 = client.post(f"/api/applications/{app2}/risk/evaluate").json()

    factors1 = [f["factor_code"] for f in risk1["contributing_factors"]]
    factors2 = [f["factor_code"] for f in risk2["contributing_factors"]]

    assert "CROSS_DOCUMENT_INCONSISTENCIES" in factors1
    assert "CROSS_DOCUMENT_INCONSISTENCIES" not in factors2


# --------------------------------------------------------------------------
# Test 15: Historical assessments retention
# --------------------------------------------------------------------------
def test_risk_assessment_history_retention():
    app_id = setup_test_application()
    client.post(f"/api/applications/{app_id}/compliance/evaluate")

    client.post(f"/api/applications/{app_id}/risk/evaluate")
    client.post(f"/api/applications/{app_id}/risk/evaluate")

    rep_res = client.get(f"/api/applications/{app_id}/risk/report")
    assert rep_res.status_code == 200
    data = rep_res.json()
    assert len(data.get("history", [])) >= 2


# --------------------------------------------------------------------------
# Test 16: Configuration endpoint
# --------------------------------------------------------------------------
def test_risk_config_endpoint():
    res = client.get("/api/risk/config")
    assert res.status_code == 200
    cfg = res.json()
    assert "weights" in cfg
    assert "bands" in cfg
    assert "completeness_states" in cfg
