import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pymupdf

import app.models
from app.main import app
from app.db.session import Base, get_db
from app.services.checklist import (
    get_checklist_for_application,
    is_eoa_category,
    is_document_match,
    EOA_DOCUMENT_CHECKLIST,
    AICTE_DOCUMENT_CHECKLIST,
)
from app.services.document_processor import process_document_sync

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


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


def create_sample_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def setup_test_app(category: str = "Extension of Approval (EoA)"):
    uid = uuid.uuid4().hex[:6].upper()
    inst_payload = {
        "institution_identifier": f"INST-EOA-{uid}",
        "name": f"National Institute of Technology {uid}",
        "institution_type": "Engineering",
        "state": "Maharashtra",
        "city": "Pune",
    }
    inst_res = client.post("/api/institutions", json=inst_payload)
    assert inst_res.status_code == 201
    inst_id = inst_res.json()["id"]

    app_payload = {
        "institution_id": inst_id,
        "application_category": category,
        "academic_year": "2026-2027",
    }
    app_res = client.post("/api/applications", json=app_payload)
    assert app_res.status_code == 201
    return app_res.json()["id"], inst_id


# =============================================================================
# 1. Verification of the 7 Exact EoA Categories and Conditions
# =============================================================================

def test_eoa_checklist_exact_seven_categories():
    """Verify that EoA returns exactly the 7 mandated categories with correct conditions."""
    checklist = get_checklist_for_application("Extension of Approval (EoA)", "2026-2027")
    assert len(checklist) == 7

    categories = [item["category"] for item in checklist]
    expected_categories = [
        "Affidavit 2",
        "AICTE Portal Payment Receipt",
        "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "Structural Stability Certificate",
        "Fire Safety Certificate",
        "Satellite Map of Land",
        "Audited Accounts",
    ]
    assert categories == expected_categories

    # 1. Affidavit 2: Mandatory
    aff = next(c for c in checklist if c["category"] == "Affidavit 2")
    assert aff["is_mandatory"] is True
    assert aff["criticality"] == "Mandatory"
    assert "Chairman/Secretary" in aff["description"]
    assert "₹100" in aff["description"]
    assert "Magistrate, Notary, or Oath Commissioner" in aff["description"]

    # 2. AICTE Portal Payment Receipt: Required if applicable (Conditional)
    pay = next(c for c in checklist if c["category"] == "AICTE Portal Payment Receipt")
    assert pay["is_mandatory"] is False
    assert pay["is_conditional"] is True
    assert "applicable" in pay["condition_description"].lower()

    # 3. Occupancy Certificate / Completion Certificate / Building Licence / Form D: Mandatory
    occ = next(c for c in checklist if c["category"] == "Occupancy Certificate / Completion Certificate / Building Licence / Form D")
    assert occ["is_mandatory"] is True
    assert occ["criticality"] == "Mandatory"
    assert "competent authority" in occ["description"].lower()

    # 4. Structural Stability Certificate: Conditional (>30 years)
    struct = next(c for c in checklist if c["category"] == "Structural Stability Certificate")
    assert struct["is_mandatory"] is False
    assert struct["is_conditional"] is True
    assert "30 years" in struct["condition_description"]
    assert "registered structural engineer" in struct["condition_description"].lower()

    # 5. Fire Safety Certificate: Mandatory
    fire = next(c for c in checklist if c["category"] == "Fire Safety Certificate")
    assert fire["is_mandatory"] is True
    assert fire["criticality"] == "Mandatory"
    assert "competent authority" in fire["description"].lower()

    # 6. Satellite Map of Land: Mandatory
    sat = next(c for c in checklist if c["category"] == "Satellite Map of Land")
    assert sat["is_mandatory"] is True
    assert sat["criticality"] == "Mandatory"
    assert "latitude/longitude" in sat["description"].lower()

    # 7. Audited Accounts: Mandatory
    audit = next(c for c in checklist if c["category"] == "Audited Accounts")
    assert audit["is_mandatory"] is True
    assert audit["criticality"] == "Mandatory"
    assert "previous year" in audit["description"].lower()


# =============================================================================
# 2. Verification of Preservation of Other 4 Application Categories
# =============================================================================

def test_non_eoa_categories_preserved():
    """Verify other application categories retain their existing checklists and are NOT replaced with EoA."""
    non_eoa_types = [
        "Increase in Intake",
        "New Institute",
        "NRI / Foreign National Quota",
        "Change of Site / Location",
    ]

    for cat in non_eoa_types:
        chk = get_checklist_for_application(cat, "2026-2027")
        cat_names = [item["category"] for item in chk]

        # Must not be the 7-item EoA checklist
        assert len(chk) != 7 or "Affidavit 2" not in cat_names

        # Category-specific verifications
        if cat in ["New Institute", "New Technical Institute"]:
            assert any("Land" in item["category"] and item["is_mandatory"] for item in chk)
            assert any(item["category"] == "Bank Manager Certificate 3" and item["is_mandatory"] for item in chk)
            assert any("Organisation" in item["category"] or "Trust" in item["category"] for item in chk)

        elif cat == "Increase in Intake":
            assert any(item["category"] == "Approved Building Plan & Sanction Order" and item["is_mandatory"] for item in chk)
            assert any(item["category"] == "Faculty Cadre & Roster Undertaking" and item["is_mandatory"] for item in chk)

        elif cat == "Change of Site / Location":
            assert any("Proposed Site" in item["category"] and item["is_mandatory"] for item in chk)
            assert any("Format 2" in item["category"] and item["is_mandatory"] for item in chk)


# =============================================================================
# 3. Verification of Checklist API Endpoint
# =============================================================================

def test_eoa_checklist_api_endpoint():
    """Test /api/applications/{id}/checklist returns exactly the 7 items with conditional properties."""
    app_id, _ = setup_test_app("Extension of Approval (EoA)")
    res = client.get(f"/api/applications/{app_id}/checklist")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 7

    # Check initial status is 'Not uploaded'
    assert all(i["status"] == "Not uploaded" for i in items)

    # Check conditional flags returned in JSON
    pay = next(i for i in items if i["category"] == "AICTE Portal Payment Receipt")
    assert pay["is_conditional"] is True
    assert pay["condition_description"] is not None

    struct = next(i for i in items if i["category"] == "Structural Stability Certificate")
    assert struct["is_conditional"] is True
    assert "30 years" in struct["condition_description"]


# =============================================================================
# 4. Verification of Document Upload, Hashing & Alias Matching
# =============================================================================

def test_eoa_document_upload_and_alias_matching():
    """Verify document upload, SHA-256 calculation, and alias matching (e.g. Fire Safety NOC -> Fire Safety Certificate)."""
    app_id, _ = setup_test_app("Extension of Approval (EoA)")

    # 1. Upload Fire Safety NOC (an alias of Fire Safety Certificate)
    fire_text = (
        "GOVERNMENT FIRE AND RESCUE SERVICES DEPARTMENT\n"
        "FIRE SAFETY NOC / CERTIFICATE\n"
        "Certificate No: CFO/PUNE/2026/7821\n"
        "Name of Institution: National Institute of Technology Pune\n"
        "Dated: 12-01-2026\n"
        "Valid until: 11-01-2029\n"
        "Issued by: Chief Fire Officer\n"
    )
    res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("fire_noc.pdf", io.BytesIO(create_sample_pdf(fire_text)), "application/pdf")},
    )
    assert res.status_code == 201
    doc_data = res.json()
    assert len(doc_data["sha256_hash"]) == 64
    doc_id = doc_data["id"]

    db = get_test_db()
    try:
        process_document_sync(db, doc_id)
    finally:
        db.close()

    # Verify checklist reflects upload under 'Fire Safety Certificate'
    chk_res = client.get(f"/api/applications/{app_id}/checklist")
    chk_items = chk_res.json()
    fire_chk = next(i for i in chk_items if i["category"] == "Fire Safety Certificate")
    assert fire_chk["uploaded_document"] is not None
    assert fire_chk["uploaded_document"]["id"] == doc_id
    assert fire_chk["status"] == "Processed"


# =============================================================================
# 5. Verification of Compliance Engine & Structural Stability Conditional Logic
# =============================================================================

def test_eoa_compliance_evaluation_and_structural_condition():
    """Verify compliance evaluation handles the 7 EoA categories and building-age conditional requirement."""
    app_id, _ = setup_test_app("Extension of Approval (EoA)")

    # A. Empty dossier should FAIL checklist rule
    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    rule_1 = next(r for r in eval_data["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert rule_1["result"] == "FAIL"
    # Mandatory items missing (5 unconditional mandatory items)
    assert len(rule_1["missing_items"]) == 5

    # For empty dossier, Land Norm (Rule 4) and Faculty Cadre (Rule 5) should be NOT_EVALUATED
    rule_4 = next(r for r in eval_data["rule_evaluations"] if r["rule_code"] == "APH-RULE-LAND-NORM")
    assert rule_4["result"] == "NOT_EVALUATED"
    rule_5 = next(r for r in eval_data["rule_evaluations"] if r["rule_code"] == "APH-RULE-FAC-PRINCIPAL")
    assert rule_5["result"] == "NOT_EVALUATED"

    # B. Upload the 5 mandatory documents with recent building completion date (2020: 6 years old <= 30)
    db = get_test_db()
    try:
        docs_to_upload = [
            ("Affidavit 2", "AFFIDAVIT 2\nChairman digital signature verified. Stamp duty: Rs. 100. Sworn before Notary Public."),
            ("Occupancy Certificate / Completion Certificate / Building Licence / Form D", "COMPLETION CERTIFICATE\nIssued by Municipal Corp. Issue Date: 15/06/2020. Valid and approved."),
            ("Fire Safety Certificate", "FIRE SAFETY CERTIFICATE\nCertificate No: CFO/2026/101. Valid until: 15-05-2028. Chief Fire Officer."),
            ("Satellite Map of Land", "SATELLITE MAP OF LAND\nLocation: Pune. Entrance Coordinates: Latitude: 18.5204 N, Longitude: 73.8567 E."),
            ("Audited Accounts", "AUDITED ACCOUNTS\nFinancial Year: 2024-2025. Balance sheet audited by Chartered Accountant. Membership No: 44102."),
        ]

        for dtype, content in docs_to_upload:
            up_res = client.post(
                f"/api/applications/{app_id}/documents",
                data={"document_type": dtype},
                files={"file": (f"{dtype.replace('/', '_')}.pdf", io.BytesIO(create_sample_pdf(content)), "application/pdf")},
            )
            assert up_res.status_code == 201
            process_document_sync(db, up_res.json()["id"])
    finally:
        db.close()

    # Re-evaluate: building age is 6 years (<= 30), so Structural Stability Certificate is NOT required -> PASS
    eval_res2 = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    eval_data2 = eval_res2.json()
    rule_1_pass = next(r for r in eval_data2["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert rule_1_pass["result"] == "PASS"

    # With documents present in EoA, Land Norm and Faculty rules evaluate to NOT_APPLICABLE
    rule_4_post = next(r for r in eval_data2["rule_evaluations"] if r["rule_code"] == "APH-RULE-LAND-NORM")
    assert rule_4_post["result"] == "NOT_APPLICABLE"
    rule_5_post = next(r for r in eval_data2["rule_evaluations"] if r["rule_code"] == "APH-RULE-FAC-PRINCIPAL")
    assert rule_5_post["result"] == "NOT_APPLICABLE"

    # C. Test older building condition (>30 years): building completion date 1985 (41 years old)
    app_id_old, _ = setup_test_app("Extension of Approval (EoA)")
    db = get_test_db()
    try:
        old_docs = [
            ("Affidavit 2", "AFFIDAVIT 2\nChairman signature. Stamp duty: Rs. 100. Sworn before Notary."),
            ("Occupancy Certificate / Completion Certificate / Building Licence / Form D", "COMPLETION CERTIFICATE\nIssue Date: 10/04/1985. Building age: 41 years old."),
            ("Fire Safety Certificate", "FIRE SAFETY CERTIFICATE\nValid until: 15-05-2028. CFO."),
            ("Satellite Map of Land", "SATELLITE MAP\nLatitude: 18.5204 N, Longitude: 73.8567 E."),
            ("Audited Accounts", "AUDITED ACCOUNTS\nFY 2024-2025. Balance sheet."),
        ]
        for dtype, content in old_docs:
            up_res = client.post(
                f"/api/applications/{app_id_old}/documents",
                data={"document_type": dtype},
                files={"file": (f"{dtype.replace('/', '_')}.pdf", io.BytesIO(create_sample_pdf(content)), "application/pdf")},
            )
            assert up_res.status_code == 201
            process_document_sync(db, up_res.json()["id"])
    finally:
        db.close()

    # Because building > 30 years old, Structural Stability Certificate condition is triggered
    eval_res_old = client.post(f"/api/applications/{app_id_old}/compliance/evaluate")
    eval_data_old = eval_res_old.json()
    rule_1_old = next(r for r in eval_data_old["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert rule_1_old["result"] == "FAIL"
    assert any("Structural Stability Certificate" in item for item in rule_1_old["missing_items"])

    # Now upload Structural Stability Certificate to satisfy the condition
    db = get_test_db()
    try:
        struct_res = client.post(
            f"/api/applications/{app_id_old}/documents",
            data={"document_type": "Structural Stability Certificate"},
            files={"file": ("stability.pdf", io.BytesIO(create_sample_pdf("STRUCTURAL STABILITY CERTIFICATE\nIssued by Registered Structural Engineer Er. K. Sharma. Stability certified.")), "application/pdf")},
        )
        assert struct_res.status_code == 201
        process_document_sync(db, struct_res.json()["id"])
    finally:
        db.close()

    eval_res_resolved = client.post(f"/api/applications/{app_id_old}/compliance/evaluate")
    eval_data_resolved = eval_res_resolved.json()
    rule_1_resolved = next(r for r in eval_data_resolved["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert rule_1_resolved["result"] == "PASS"
