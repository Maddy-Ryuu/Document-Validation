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
    is_increase_intake_category,
    is_new_institute_category,
    is_nri_fn_category,
    is_change_site_category,
    is_document_match,
    EOA_DOCUMENT_CHECKLIST,
    INCREASE_INTAKE_DOCUMENT_CHECKLIST,
    NEW_INSTITUTE_DOCUMENT_CHECKLIST,
    NRI_FN_QUOTA_DOCUMENT_CHECKLIST,
    CHANGE_SITE_DOCUMENT_CHECKLIST,
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


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


def create_sample_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def setup_test_app(category: str):
    uid = uuid.uuid4().hex[:6].upper()
    inst_payload = {
        "institution_identifier": f"INST-CAT-{uid}",
        "name": f"Apex Institute of Technology {uid}",
        "institution_type": "Engineering",
        "state": "Maharashtra",
        "city": "Mumbai",
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
    return app_res.json()["id"], inst_id, inst_payload["name"]


# =============================================================================
# SCENARIOS 1-7: CATEGORY CONFIGURATION & CHECKLIST STRUCTURE
# =============================================================================

def test_01_eoa_continues_seven_document_checklist():
    """1. EoA continues to display its existing seven-document checklist."""
    checklist = get_checklist_for_application("Extension of Approval (EoA)", "2026-2027")
    assert len(checklist) == 7
    categories = [c["category"] for c in checklist]
    expected = [
        "Affidavit 2",
        "AICTE Portal Payment Receipt",
        "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "Structural Stability Certificate",
        "Fire Safety Certificate",
        "Satellite Map of Land",
        "Audited Accounts",
    ]
    assert categories == expected
    assert is_eoa_category("Extension of Approval (EoA)") is True


def test_02_increase_in_intake_checklist_configuration():
    """2. Increase in Intake displays its configured base and applicable intake-specific requirements."""
    checklist = get_checklist_for_application("Increase in Intake", "2026-2027")
    assert len(checklist) == 11
    categories = [c["category"] for c in checklist]
    assert "Affidavit 2" in categories
    assert "University Affiliation / State Govt Permission" in categories
    assert "Approved Building Plan & Sanction Order" in categories
    assert "Faculty Cadre & Roster Undertaking" in categories
    assert "Architect Certificate of Completion & Barrier-Free Access" in categories
    assert "Accreditation Certificate (NBA / NAAC)" in categories
    assert is_increase_intake_category("Increase in Intake") is True


def test_03_new_technical_institute_checklist_configuration():
    """3. New Technical Institute displays its configured 11 institutional establishment documents."""
    checklist = get_checklist_for_application("New Technical Institute", "2026-2027")
    assert len(checklist) == 11
    categories = [c["category"] for c in checklist]
    expected = [
        "Approved Building Plan",
        "Affidavit 2",
        "Applicant Organisation Resolution (Format 3)",
        "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "Fire Safety Certificate",
        "Bank Manager Certificate 3",
        "Complete Online Application & Prescribed Hard Copy",
        "Organisation Registration Documents",
        "Board of Governors Composition",
        "Land / Building Ownership Evidence",
        "Conditional Documents for Section 8 / PPP / BOT Arrangements",
    ]
    assert categories == expected
    assert is_new_institute_category("New Technical Institute") is True
    assert is_new_institute_category("New Institute") is True


def test_04_nri_foreign_national_quota_checklist_configuration():
    """4. NRI quota and foreign-national quota apply the correct subtype-specific checklist."""
    checklist = get_checklist_for_application("NRI / Foreign National Quota", "2026-2027")
    assert len(checklist) == 8
    categories = [c["category"] for c in checklist]
    assert "Affidavit 2" in categories
    assert "Trust / Society Resolution for NRI / FN Quota (Format 3)" in categories
    assert "University Affiliation / State Board Approval for Quota Seats" in categories
    assert "Accreditation / Eligibility Proof for Supernumerary FN Seats" in categories
    assert is_nri_fn_category("NRI / Foreign National Quota") is True


def test_05_change_of_site_location_checklist_configuration():
    """5. Change of Site / Location distinguishes existing and proposed sites."""
    checklist = get_checklist_for_application("Change of Site / Location", "2026-2027")
    assert len(checklist) == 11
    categories = [c["category"] for c in checklist]
    assert "Existing Institution Approval & Clearance Record" in categories
    assert "Affiliating University / Board NOC (Format 2)" in categories
    assert "Applicant Organisation Resolution (Format 3)" in categories
    assert "Land Ownership and Title Certificate (Proposed Site)" in categories
    assert "Land Use Certificate & Non-Encumbrance Certificate (Proposed Site)" in categories
    assert "Approved Building Plan (Proposed Site)" in categories
    assert "Occupancy Certificate / Completion Certificate (Proposed Site)" in categories
    assert "Fire Safety Certificate (Proposed Site)" in categories
    assert is_change_site_category("Change of Site / Location") is True


def test_06_conditional_documents_not_marked_missing_when_inapplicable():
    """6. Conditional documents are not marked missing when conditions do not apply."""
    app_id, _, _ = setup_test_app("New Technical Institute")

    checklist_res = client.get(f"/api/applications/{app_id}/checklist")
    assert checklist_res.status_code == 200
    items = checklist_res.json()
    bog_item = next(i for i in items if i["category"] == "Board of Governors Composition")
    assert bog_item["is_conditional"] is True
    assert bog_item["is_mandatory"] is False
    assert "standalone PGDM" in bog_item["condition_description"]

    sec8_item = next(i for i in items if "Section 8" in i["category"])
    assert sec8_item["is_conditional"] is True
    assert sec8_item["is_mandatory"] is False


def test_07_unknown_or_unconfirmed_quota_subtype_requires_review():
    """7. Unknown or unconfirmed applicability is not silently treated as compliant."""
    app_id, _, _ = setup_test_app("NRI / Foreign National Quota")

    pdf = create_sample_pdf("Resolution passed by Society for quota seats. Certificate No: RES-2026-101. Dated: 10/01/2026.")
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Trust / Society Resolution for NRI / FN Quota (Format 3)"},
        files={"file": ("resolution.pdf", pdf, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_nri = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-NRI-FN-SUBTYPE")
    assert rule_nri["result"] == "NEEDS_REVIEW"
    assert "Exact quota subtype" in rule_nri["explanation"]


# =============================================================================
# SCENARIOS 8-18: DOCUMENT VERIFICATION & RULE EVALUATIONS
# =============================================================================

def test_08_correct_document_type_with_sufficient_evidence():
    """8. Correct document type with sufficient evidence passes rule check."""
    app_id, _, inst_name = setup_test_app("New Technical Institute")

    pdf_bank = create_sample_pdf(
        f"Bank Manager Certificate 3. In favour of {inst_name}.\n"
        "FDR No: FDR-99214-SBI. Deposit Amount: Rs. 1,00,00,000.\n"
        "Issued by: State Bank of India. Dated: 12/01/2026."
    )
    up_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Bank Manager Certificate 3"},
        files={"file": ("bank_cert.pdf", pdf_bank, "application/pdf")},
    )
    assert up_res.status_code == 201

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_bank = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-NEW-INST-BANK")
    assert rule_bank["result"] == "PASS"


def test_09_wrong_document_type_uploaded_under_category():
    """9. Missing required documents when wrong type uploaded triggers missing document check."""
    app_id, _, _ = setup_test_app("New Technical Institute")

    pdf_misc = create_sample_pdf("Water safety test certificate.")
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Other Regulatory Supporting Documents"},
        files={"file": ("water_test.pdf", pdf_misc, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_chk = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
    assert rule_chk["result"] == "FAIL"
    assert len(rule_chk["missing_items"]) >= 5


def test_10_required_document_missing_in_intake_increase():
    """10. Required document missing (e.g. University Affiliation for Intake Increase)."""
    app_id, _, _ = setup_test_app("Increase in Intake")

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_affil = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-INTAKE-AFFILIATION")
    assert rule_affil["result"] == "FAIL"
    assert "missing" in rule_affil["explanation"].lower()


def test_11_unreadable_or_incomplete_document_triggers_review():
    """11. Document with unextractable fields triggers review rather than silent pass."""
    app_id, _, _ = setup_test_app("New Technical Institute")

    pdf_blank = create_sample_pdf("Land document without extent or acreage specified.")
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Land / Building Ownership Evidence"},
        files={"file": ("land_deed.pdf", pdf_blank, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_land = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-LAND-NORM")
    assert rule_land["result"] == "NEEDS_REVIEW"


def test_12_institution_names_that_match():
    """12. Extracted institution names consistent across documents pass identity matching."""
    app_id, _, inst_name = setup_test_app("Increase in Intake")

    pdf1 = create_sample_pdf(f"Institute: {inst_name}\nCertificate No: CFO/2026/01\nValid until: 15/01/2029")
    pdf2 = create_sample_pdf(f"Name of the Institution: {inst_name}\nOrder No: UNIV/AFFIL/881\nApproved: Additional 60 seats")

    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("fire_cert.pdf", pdf1, "application/pdf")},
    )
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "University Affiliation / State Govt Permission"},
        files={"file": ("univ_affil.pdf", pdf2, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_id = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
    assert rule_id["result"] == "PASS"


def test_13_genuine_institution_name_conflict():
    """13. Genuine institution name or identifier conflict flags FAIL."""
    app_id, _, inst_name = setup_test_app("New Technical Institute")

    pdf_alien = create_sample_pdf("Institute: Completely Alien Polytech of Northern Valley\nCert: NOC-1122")
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("alien_fire.pdf", pdf_alien, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_id = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
    assert rule_id["result"] == "FAIL"


def test_14_ocr_fragment_triggers_review():
    """14. OCR fragment triggers review rather than definitive mismatch."""
    app_id, _, inst_name = setup_test_app("New Technical Institute")

    pdf_fragment = create_sample_pdf("Institute: XYZ\nNOC: 123")
    up_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("fragment_doc.pdf", pdf_fragment, "application/pdf")},
    )
    assert up_res.status_code == 201

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_id = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
    assert rule_id["result"] in ("NEEDS_REVIEW", "NOT_EVALUATED")


def test_15_future_date_synthetic_authenticity_unverified():
    """15. Certificate with future date but marked as synthetic summary triggers NEEDS_REVIEW."""
    app_id, _, _ = setup_test_app("Increase in Intake")

    pdf_synth = create_sample_pdf(
        "Fire Safety NOC. Valid until: 15/01/2028. SYNTHETIC TEST DOCUMENT - not an official record."
    )
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("synthetic_fire.pdf", pdf_synth, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_fire = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-EXPIRY")
    assert rule_fire["result"] == "NEEDS_REVIEW"
    assert "UNVERIFIED" in rule_fire["explanation"]


def test_16_change_of_site_old_site_reuse_detection():
    """16. Change of site detects and blocks old site certificate reuse."""
    app_id, _, _ = setup_test_app("Change of Site / Location")

    pdf_old_site = create_sample_pdf(
        "Land Deed. Old campus only. Current location certificate reused."
    )
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Land Ownership and Title Certificate (Proposed Site)"},
        files={"file": ("old_land.pdf", pdf_old_site, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_site = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-SITE-LOCATION-DISTINCTION")
    assert rule_site["result"] == "FAIL"
    assert "old-site" in rule_site["explanation"].lower()


def test_17_duplicate_file_collision_detection():
    """17. Duplicate file uploaded to two slots triggers duplicate collision protection."""
    app_id, _, _ = setup_test_app("New Technical Institute")

    identical_pdf = create_sample_pdf("Identical binary content shared across two checklist slots.")
    res1 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Approved Building Plan"},
        files={"file": ("plan.pdf", identical_pdf, "application/pdf")},
    )
    assert res1.status_code == 201

    res2 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("duplicate_fire.pdf", identical_pdf, "application/pdf")},
    )
    assert res2.status_code in (400, 409)
    assert any(w in res2.json()["detail"].lower() for w in ["identical", "duplicate"])


def test_18_pending_satellite_gis_clearly_identified():
    """18. Unsupported / pending gateway checks are clearly marked as NOT_APPLICABLE / pending confirmation."""
    app_id, _, _ = setup_test_app("New Technical Institute")

    pdf = create_sample_pdf("Building Plan. Sanction: BP-101.")
    client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Approved Building Plan"},
        files={"file": ("plan.pdf", pdf, "application/pdf")},
    )

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    rule_gis = next(r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-PENDING-SATELLITE-GIS")
    assert rule_gis["result"] == "NOT_APPLICABLE"
    assert rule_gis.get("is_pending_confirmation") is True
