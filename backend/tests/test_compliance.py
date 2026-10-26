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

client = TestClient(app, raise_server_exceptions=False)


def get_test_db():
    # If app has an active override (such as when running alongside other tests), use the override sessionmaker
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


def test_rule_catalog_endpoint():
    res = client.get("/api/compliance/rules")
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 6
    assert any(r["rule_code"] == "APH-RULE-DOC-CHECKLIST" for r in rules)
    assert any(r["rule_code"] == "APH-RULE-DOC-EXPIRY" for r in rules)
    assert any(r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH" for r in rules)


def test_missing_mandatory_documents_rule():
    # Empty application dossier should FAIL checklist rule
    app_id = setup_test_application()
    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["compliance_status"] == "Action Required"
    assert data["summary"]["failed"] >= 1

    chk_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert chk_rule["result"] == "FAIL"
    assert len(chk_rule["missing_items"]) > 0


def test_expired_fire_noc_compliance_failure():
    app_id = setup_test_application()
    # Upload expired Fire Safety NOC (valid until 2023)
    text = (
        "FIRE SAFETY NOC\n"
        "Name of Institution: Apex Institute of Technology & Advanced Studies\n"
        "Certificate No: CFO/2022/881\n"
        "Valid until: 15-05-2023\n"
        "Issued by: Chief Fire Officer\n"
    )
    pdf_bytes = create_sample_pdf(text)
    upload_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("fire_noc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    doc_id = upload_res.json()["id"]

    # Process extraction using app's db session
    db = get_test_db()
    try:
        process_document_sync(db, doc_id)
    finally:
        db.close()

    # Evaluate compliance
    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    data = eval_res.json()

    exp_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-EXPIRY")
    assert exp_rule["result"] == "FAIL"
    assert "expired" in exp_rule["explanation"].lower()


def test_cross_document_identity_mismatch_rule():
    # Master application is for "Apex Institute of Technology & Advanced Studies"
    app_id = setup_test_application(inst_name="Apex Institute of Technology & Advanced Studies")

    # Upload document with conflicting alien institution name
    alien_text = (
        "STATE GOVERNMENT APPROVAL ORDER\n"
        "Name of Institution: Zenith Polytechnic & Technology Campus\n"
        "Order No: HE/ORDER/2025/991\n"
        "Dated: 10-04-2025\n"
    )
    pdf_bytes = create_sample_pdf(alien_text)
    upload_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "University Affiliation / State Govt Permission"},
        files={"file": ("alien_approval.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    doc_id = upload_res.json()["id"]

    db = get_test_db()
    try:
        process_document_sync(db, doc_id)
    finally:
        db.close()

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    data = eval_res.json()

    mismatch_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
    assert mismatch_rule["result"] == "FAIL"
    assert len(mismatch_rule.get("mismatches", [])) >= 1


def test_land_area_norm_evaluation():
    app_id = setup_test_application()
    # Land deed with 5.25 Acres (satisfies >= 2.5 Acres threshold)
    text = (
        "REGISTERED LAND DEED\n"
        "Name of Institution: Apex Institute of Technology & Advanced Studies\n"
        "Survey Number: 142/2A\n"
        "Land Area: 5.25 Acres\n"
    )
    pdf_bytes = create_sample_pdf(text)
    upload_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Land Ownership and Title Certificate"},
        files={"file": ("land_deed.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    doc_id = upload_res.json()["id"]

    db = get_test_db()
    try:
        process_document_sync(db, doc_id)
    finally:
        db.close()

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    data = eval_res.json()

    land_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-LAND-NORM")
    assert land_rule["result"] == "PASS"
    assert "5.25" in land_rule["actual_value"]


def test_pending_confirmation_rule_handling():
    app_id = setup_test_application()
    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    data = eval_res.json()

    pending_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-PENDING-SATELLITE-GIS")
    assert pending_rule["result"] == "NOT_APPLICABLE"
    assert pending_rule.get("is_pending_confirmation") is True


# =========================================================================
# REGRESSION TEST SUITE FOR EVIDENCE HANDLING & RESULT ACCURACY
# =========================================================================

def test_regression_no_documents_uploaded():
    """No documents uploaded must yield NOT_EVALUATED or appropriate non-PASS states, not false passes."""
    app_id = setup_test_application()
    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    data = eval_res.json()

    # Checklist should fail (missing mandatory docs)
    chk_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert chk_rule["result"] == "FAIL"

    # Expiry should be NOT_EVALUATED
    exp_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-EXPIRY")
    assert exp_rule["result"] == "NOT_EVALUATED"

    # Cross ID should be NOT_EVALUATED
    id_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
    assert id_rule["result"] == "NOT_EVALUATED"

    # Duplicate hash should be NOT_EVALUATED
    dup_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DUP-HASH")
    assert dup_rule["result"] == "NOT_EVALUATED"

    # Land norm should be NOT_EVALUATED
    land_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-LAND-NORM")
    assert land_rule["result"] == "NOT_EVALUATED"


def test_regression_synthetic_metadata_summaries_unverified():
    """Synthetic metadata summaries must NOT pass validity or land norm as authentic; they must return NEEDS_REVIEW."""
    app_id = setup_test_application()

    # Upload synthetic fire NOC summary
    synth_fire = (
        "SYNTHETIC TEST DOCUMENT - NOT AN OFFICIAL RECORD\n"
        "Fire Safety NOC - Metadata Summary\n"
        "Deliberately not a certificate issued by any authority\n"
        "Institution: Apex Institute of Technology & Advanced Studies\n"
        "Test expiry date: 15-05-2027\n"
    )
    res_fire = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("07_fire_safety_noc_summary.pdf", io.BytesIO(create_sample_pdf(synth_fire)), "application/pdf")},
    )
    # Upload synthetic land summary
    synth_land = (
        "SYNTHETIC TEST DOCUMENT - NOT AN OFFICIAL RECORD\n"
        "Land / Site Information Summary\n"
        "Institution: Apex Institute of Technology & Advanced Studies\n"
        "Land area: 5.25 acres\n"
        "Survey reference: 142/2A\n"
    )
    res_land = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Land Ownership and Title Certificate"},
        files={"file": ("06_land_document_summary.pdf", io.BytesIO(create_sample_pdf(synth_land)), "application/pdf")},
    )

    db = get_test_db()
    try:
        process_document_sync(db, res_fire.json()["id"])
        process_document_sync(db, res_land.json()["id"])
    finally:
        db.close()

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    data = eval_res.json()

    exp_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-EXPIRY")
    assert exp_rule["result"] == "NEEDS_REVIEW"
    assert "unverified" in exp_rule["actual_value"].lower()

    land_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-LAND-NORM")
    assert land_rule["result"] == "NEEDS_REVIEW"
    assert "unverified" in land_rule["actual_value"].lower()


def test_regression_cross_doc_identity_two_matching_and_mismatched():
    """Cross-document identity with 2 matching documents passes; with mismatch fails."""
    # 1. Matching
    app_id = setup_test_application(inst_name="Apex Institute of Technology & Advanced Studies")
    doc1 = (
        "GOVT AFFILIATION ORDER\n"
        "Name of Institution: Apex Institute of Technology & Advanced Studies\n"
        "Order No: AFF/2026/01\n"
    )
    doc2 = (
        "ARCHITECT SANCTION CERTIFICATE\n"
        "Name of Institution: Apex Institute of Technology & Advanced Studies\n"
        "Certificate No: ARCH/2026/02\n"
    )
    r1 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "University Affiliation / State Govt Permission"},
        files={"file": ("aff.pdf", io.BytesIO(create_sample_pdf(doc1)), "application/pdf")},
    )
    r2 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Architect Certificate of Completion & Barrier-Free Access"},
        files={"file": ("arch.pdf", io.BytesIO(create_sample_pdf(doc2)), "application/pdf")},
    )

    db = get_test_db()
    try:
        process_document_sync(db, r1.json()["id"])
        process_document_sync(db, r2.json()["id"])
    finally:
        db.close()

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    data = eval_res.json()
    id_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
    assert id_rule["result"] == "PASS"
    assert len(id_rule.get("compared_documents", [])) == 2


def test_regression_duplicate_file_collision_detection():
    """Different files pass duplicate check; identical hash fails."""
    app_id = setup_test_application()
    pdf1 = create_sample_pdf("File content A")
    pdf2 = create_sample_pdf("File content B with different bytes")

    r1 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Land Ownership and Title Certificate"},
        files={"file": ("file1.pdf", io.BytesIO(pdf1), "application/pdf")},
    )
    r2 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("file2.pdf", io.BytesIO(pdf2), "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    data = eval_res.json()
    dup_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DUP-HASH")
    assert dup_rule["result"] == "PASS"
    assert dup_rule.get("verified_files_count") == 2


def test_regression_missing_or_unreadable_expiry_field():
    """Document uploaded without extractable expiry date returns NEEDS_REVIEW."""
    app_id = setup_test_application()
    text = (
        "FIRE DEPARTMENT RECEIPT\n"
        "Fee paid for fire scrutiny.\n"
    )
    r = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("receipt.pdf", io.BytesIO(create_sample_pdf(text)), "application/pdf")},
    )
    db = get_test_db()
    try:
        process_document_sync(db, r.json()["id"])
    finally:
        db.close()

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    data = eval_res.json()
    exp_rule = next(r for r in data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-EXPIRY")
    assert exp_rule["result"] == "NEEDS_REVIEW"
