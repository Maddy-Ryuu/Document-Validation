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


def create_test_application():
    unique_id = uuid.uuid4().hex[:6].upper()
    inst_payload = {
        "institution_identifier": f"INST-{unique_id}",
        "name": f"Delhi Technical University {unique_id}",
        "institution_type": "Engineering",
        "state": "Delhi",
        "city": "New Delhi",
    }
    inst_res = client.post("/api/institutions", json=inst_payload)
    assert inst_res.status_code == 201
    inst_id = inst_res.json()["id"]

    app_payload = {
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
    }
    app_res = client.post("/api/applications", json=app_payload)
    assert app_res.status_code == 201
    return app_res.json()["id"]


def test_phase1_regression():
    app_id = create_test_application()
    assert app_id is not None


def test_checklist_endpoint():
    app_id = create_test_application()
    res = client.get(f"/api/applications/{app_id}/checklist")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0
    assert any(i["category"] == "Fire Safety NOC" for i in items)
    assert all(i["status"] == "Not uploaded" for i in items)


def test_pdf_document_upload_and_extraction():
    app_id = create_test_application()

    sample_text = (
        "GOVERNMENT OF NCT OF DELHI - DIRECTORATE OF FIRE SERVICES\n"
        "FIRE SAFETY NOC\n"
        "Certificate No.: DFS/NOC/2026/8941\n"
        "Name of the Institution: Delhi Technical University Test Campus\n"
        "Dated: 15/01/2026\n"
        "Valid until: 14/01/2029\n"
        "Issued by: Chief Fire Officer, Delhi Fire Service\n"
        "This is to certify that the institutional building complies with fire safety norms."
    )
    pdf_data = create_sample_pdf(sample_text)

    # 1. Upload
    upload_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("fire_noc.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["document_type"] == "Fire Safety NOC"
    assert doc_data["sha256_hash"] is not None
    assert doc_data["version"] == 1
    doc_id = doc_data["id"]

    # 2. Check document file streaming
    file_res = client.get(f"/api/documents/{doc_id}/file")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"] == "application/pdf"
    assert len(file_res.content) == len(pdf_data)

    # 3. Synchronous OCR extraction check
    from app.services.document_processor import process_document_sync
    db = TestingSessionLocal()
    process_document_sync(db, doc_id)
    db.close()

    # 4. Fetch extraction
    ext_res = client.get(f"/api/documents/{doc_id}/extraction")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()
    assert ext_data["page_count"] == 1
    fields = ext_data["structured_fields"]
    assert "certificate_number" in fields
    assert "DFS/NOC/2026/8941" in fields["certificate_number"]["value"]
    assert "Delhi Technical University" in fields["institution_name"]["value"]
    assert "14/01/2029" in fields["valid_until"]["value"]


def test_field_correction_and_audit():
    app_id = create_test_application()
    pdf_data = create_sample_pdf("NOC No.: FIRE-12345 Valid until: 01/01/2027")

    upload_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("fire_test.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    db = TestingSessionLocal()
    from app.services.document_processor import process_document_sync
    process_document_sync(db, doc_id)
    db.close()

    # Apply correction
    correction_payload = {
        "field_name": "certificate_number",
        "corrected_value": "FIRE-12345-CORRECTED",
        "reason": "Officer verified against State Fire Registry and added regional suffix",
    }
    patch_res = client.patch(f"/api/documents/{doc_id}/extraction", json=correction_payload)
    assert patch_res.status_code == 200
    updated_fields = patch_res.json()["structured_fields"]
    assert updated_fields["certificate_number"]["value"] == "FIRE-12345-CORRECTED"
    assert updated_fields["certificate_number"]["corrected"] is True
    assert updated_fields["certificate_number"]["original_extracted_value"] == "FIRE-12345"


def test_document_replacement_and_versioning():
    app_id = create_test_application()
    pdf1 = create_sample_pdf("Initial Version 1")
    pdf2 = create_sample_pdf("Updated Version 2 (Replaced)")

    # Upload version 1
    res1 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("v1.pdf", io.BytesIO(pdf1), "application/pdf")},
    )
    assert res1.status_code == 201
    doc1_id = res1.json()["id"]
    assert res1.json()["version"] == 1

    # Upload replacement (version 2)
    res2 = client.post(
        f"/api/applications/{app_id}/documents",
        data={
            "document_type": "Fire Safety NOC",
            "replaces_document_id": doc1_id,
        },
        files={"file": ("v2.pdf", io.BytesIO(pdf2), "application/pdf")},
    )
    assert res2.status_code == 201
    doc2_id = res2.json()["id"]
    assert res2.json()["version"] == 2
    assert res2.json()["replaces_document_id"] == doc1_id

    # Check version history
    hist_res = client.get(f"/api/documents/{doc2_id}/versions")
    assert hist_res.status_code == 200
    versions = hist_res.json()
    assert len(versions) == 2
    assert versions[0]["id"] == doc2_id
    assert versions[1]["id"] == doc1_id


def test_duplicate_upload_rejection():
    app_id = create_test_application()
    pdf_data = create_sample_pdf("Constant File Content")

    # Upload 1
    res1 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("test.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    assert res1.status_code == 201

    # Upload 2 identical
    res2 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("test.pdf", io.BytesIO(pdf_data), "application/pdf")},
    )
    assert res2.status_code == 400
    assert "Identical file already uploaded" in res2.json()["detail"]


def test_invalid_file_format():
    app_id = create_test_application()
    bad_file = io.BytesIO(b"malicious script")
    res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety NOC"},
        files={"file": ("script.exe", bad_file, "application/octet-stream")},
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_application_detail_loads_after_document_upload_regression():
    """
    Regression test for: Application detail 500 error after document upload
    caused by missing DocumentResponse updated_at field mapping in ApplicationService.
    """
    app_id = create_test_application()
    
    # 1. Detail must load cleanly before upload
    detail_before = client.get(f"/api/applications/{app_id}")
    assert detail_before.status_code == 200
    assert len(detail_before.json()["documents"]) == 0

    # 2. Upload valid PDF
    pdf_bytes = create_sample_pdf("Valid AICTE Affiliation Document")
    upload_res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "University Affiliation / State Govt Permission"},
        files={"file": ("affiliation.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 201

    # 3. Application detail must load with status 200 and document list populated
    detail_after = client.get(f"/api/applications/{app_id}")
    assert detail_after.status_code == 200
    app_data = detail_after.json()
    assert len(app_data["documents"]) == 1
    doc = app_data["documents"][0]
    assert doc["document_type"] == "University Affiliation / State Govt Permission"
    assert "updated_at" in doc
    assert doc["updated_at"] is not None

    # 4. Compliance report endpoint must also load without error
    rep = client.get(f"/api/applications/{app_id}/compliance/report")
    assert rep.status_code == 200
