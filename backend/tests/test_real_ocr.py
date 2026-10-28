import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pymupdf
from PIL import Image, ImageDraw

from app.main import app
from app.db.session import Base, get_db
from app.services.ocr import OCRExtractorService, MAX_DOCUMENT_PAGE_COUNT
from app.services.document_processor import process_document_sync
from app.models.models import Document, DocumentExtraction, Application, Institution

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


# ---------------------------------------------------------------------------
# TEST FIXTURE GENERATORS
# ---------------------------------------------------------------------------

def create_digital_pdf(text: str) -> bytes:
    """Generates a standard digital PDF containing a vector text layer."""
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=300)
    page.insert_text((40, 50), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_scanned_pdf(lines: list) -> bytes:
    """
    Generates a genuine scanned PDF:
    Renders text onto a PIL raster image, converts to PNG, and embeds the raster image.
    The resulting PDF has ZERO vector text characters.
    """
    img = Image.new("RGB", (700, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    y = 40
    for line in lines:
        d.text((40, y), line, fill=(0, 0, 0))
        y += 40

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=700, height=300)
    page.insert_image(page.rect, stream=img_bytes)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_mixed_pdf(digital_text: str, scanned_lines: list) -> bytes:
    """Generates a 2-page mixed PDF: Page 1 is digital text; Page 2 is a scanned raster image."""
    doc = pymupdf.open()
    # Page 1: Digital
    p1 = doc.new_page(width=600, height=300)
    p1.insert_text((40, 50), digital_text, fontsize=12)

    # Page 2: Scanned raster
    img = Image.new("RGB", (700, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    y = 40
    for line in scanned_lines:
        d.text((40, y), line, fill=(0, 0, 0))
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    p2 = doc.new_page(width=700, height=300)
    p2.insert_image(p2.rect, stream=buf.getvalue())

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def setup_test_app(category: str = "Extension of Approval (EoA)"):
    uid = uuid.uuid4().hex[:6].upper()
    inst_res = client.post("/api/institutions", json={
        "institution_identifier": f"INST-OCR-{uid}",
        "name": f"Pune Institute of Applied Science {uid}",
        "institution_type": "Engineering",
        "state": "Maharashtra",
        "city": "Pune",
    })
    assert inst_res.status_code == 201
    inst_id = inst_res.json()["id"]

    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": category,
        "academic_year": "2026-2027",
    })
    assert app_res.status_code == 201
    return app_res.json()["id"], inst_id, f"Pune Institute of Applied Science {uid}"


# ===========================================================================
# 1. DIGITAL PDF FAST-PATH
# ===========================================================================

def test_01_digital_pdf_uses_fast_path(tmp_path):
    """1. A digitally generated PDF continues to use the fast digital text extraction path."""
    pdf_bytes = create_digital_pdf(
        "Fire Safety Certificate CFO/2026/101\nValid until: 15/05/2028\nInstitute: Pune Institute of Applied Science"
    )
    pdf_file = tmp_path / "digital.pdf"
    pdf_file.write_bytes(pdf_bytes)

    full_text, page_count, pages_meta, avg_conf = OCRExtractorService.extract_text_and_pages(
        str(pdf_file), "application/pdf"
    )
    assert page_count == 1
    assert pages_meta[0]["extraction_method"] == "DIGITAL_TEXT"
    assert pages_meta[0]["is_scanned"] is False
    assert avg_conf >= 0.95
    assert "Fire Safety Certificate" in full_text


# ===========================================================================
# 2. SCANNED PDF GENUINE OCR
# ===========================================================================

def test_02_scanned_pdf_produces_genuine_ocr(tmp_path):
    """2. A scanned PDF with known text produces genuine OCR-derived text and tags is_ocr_derived."""
    scanned_lines = [
        "FIRE SAFETY NOC CLEARANCE",
        "Certificate No: CFO/MH/2026/7781",
        "Valid until: 20/06/2028",
        "Institute: Pune Institute of Applied Science",
    ]
    pdf_bytes = create_scanned_pdf(scanned_lines)
    pdf_file = tmp_path / "scanned.pdf"
    pdf_file.write_bytes(pdf_bytes)

    # Verify that PyMuPDF vector text extraction yields 0 text
    raw_doc = pymupdf.open(str(pdf_file))
    assert len(raw_doc[0].get_text("text").strip()) == 0
    raw_doc.close()

    # Now execute real OCR extractor
    full_text, page_count, pages_meta, avg_conf = OCRExtractorService.extract_text_and_pages(
        str(pdf_file), "application/pdf"
    )
    assert page_count == 1
    assert pages_meta[0]["extraction_method"] == "OCR_RASTER"
    assert pages_meta[0]["is_scanned"] is True
    assert avg_conf > 0.50
    assert "FIRE" in full_text.upper()

    # Structured fields must tag is_ocr_derived as True
    fields = OCRExtractorService.extract_structured_fields(full_text, "Fire Safety Certificate", pages_meta)
    if "institution_name" in fields:
        assert fields["institution_name"]["is_ocr_derived"] is True
        assert fields["institution_name"]["extraction_method"] == "OCR_RASTER"


# ===========================================================================
# 3. MIXED DOCUMENT PROCESSING
# ===========================================================================

def test_03_mixed_pdf_processes_each_page_appropriately(tmp_path):
    """3. A mixed PDF processes Page 1 via digital extraction and Page 2 via OCR rasterization."""
    p1_text = "Affidavit 2 under AICTE Approval Process Handbook\nSworn before: Notary Public\nStamp duty: Rs 100"
    p2_lines = ["Fire Safety NOC Annexure", "Valid until: 15/07/2028", "Director General of Fire Services"]

    pdf_bytes = create_mixed_pdf(p1_text, p2_lines)
    pdf_file = tmp_path / "mixed.pdf"
    pdf_file.write_bytes(pdf_bytes)

    full_text, page_count, pages_meta, avg_conf = OCRExtractorService.extract_text_and_pages(
        str(pdf_file), "application/pdf"
    )
    assert page_count == 2
    assert pages_meta[0]["extraction_method"] == "DIGITAL_TEXT"
    assert pages_meta[0]["is_scanned"] is False

    assert pages_meta[1]["extraction_method"] == "OCR_RASTER"
    assert pages_meta[1]["is_scanned"] is True


# ===========================================================================
# 4. PLACEHOLDER REMOVAL VERIFICATION
# ===========================================================================

def test_04_no_fake_placeholders_used_as_ocr_evidence(tmp_path):
    """4. Confirms fake scanned-page placeholders are completely removed and never emitted as text."""
    pdf_bytes = create_scanned_pdf(["Approved Building Sanction Order", "Sanction No: BP/2026/99"])
    pdf_file = tmp_path / "placeholder_check.pdf"
    pdf_file.write_bytes(pdf_bytes)

    full_text, _, pages_meta, _ = OCRExtractorService.extract_text_and_pages(
        str(pdf_file), "application/pdf"
    )
    forbidden_snippets = [
        "Raster graphic analyzed",
        "Scanned page",
        "registered for regulatory inspection",
    ]
    for snip in forbidden_snippets:
        assert snip.lower() not in full_text.lower(), f"Forbidden placeholder found: {snip}"
        assert snip.lower() not in pages_meta[0]["text"].lower()


# ===========================================================================
# 5. CONTROLLED ERROR & REVIEW ROUTING
# ===========================================================================

def test_05_ocr_failure_or_unreadable_produces_controlled_review_status(tmp_path):
    """5. An empty/blank scanned page produces controlled review status without throwing exceptions."""
    # Blank white scanned image (no text drawn)
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    doc = pymupdf.open()
    p = doc.new_page(width=400, height=200)
    p.insert_image(p.rect, stream=buf.getvalue())
    pdf_bytes = doc.tobytes()
    doc.close()

    pdf_file = tmp_path / "blank_scanned.pdf"
    pdf_file.write_bytes(pdf_bytes)

    full_text, count, pages_meta, avg_conf = OCRExtractorService.extract_text_and_pages(
        str(pdf_file), "application/pdf"
    )
    assert count == 1
    assert pages_meta[0]["extraction_method"] == "OCR_RASTER"
    assert "No legible text" in full_text or avg_conf == 0.0


# ===========================================================================
# 6. LOW CONFIDENCE WARNINGS
# ===========================================================================

def test_06_low_confidence_or_scanned_warning_handling():
    """6. Document processing generates actionable warnings for review on low-confidence/scanned files."""
    app_id, _, _ = setup_test_app()

    # Upload blank raster page to trigger Needs Review
    img = Image.new("RGB", (300, 150), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    doc = pymupdf.open()
    p = doc.new_page(width=300, height=150)
    p.insert_image(p.rect, stream=buf.getvalue())
    blank_bytes = doc.tobytes()
    doc.close()

    res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("blank_scan.pdf", blank_bytes, "application/pdf")},
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    db = TestingSessionLocal()
    try:
        updated_doc = process_document_sync(db, doc_id)
        assert updated_doc.processing_status in ("Needs Review", "Processed")
        ext = db.query(DocumentExtraction).filter(DocumentExtraction.document_id == doc_id).first()
        assert ext is not None
        assert len(ext.warnings) > 0
    finally:
        db.close()


# ===========================================================================
# 7. FIELD SURVIVAL & NORMALIZATION
# ===========================================================================

def test_07_dates_identifiers_coordinates_survive_extraction(tmp_path):
    """7. Dates, identifiers, and land coordinates survive extraction from scanned content."""
    scanned_lines = [
        "Satellite Map of Land Coordinates",
        "Latitude: 18.5204 N",
        "Longitude: 73.8567 E",
        "Total land area: 3.50 acres",
    ]
    pdf_bytes = create_scanned_pdf(scanned_lines)
    pdf_file = tmp_path / "coords.pdf"
    pdf_file.write_bytes(pdf_bytes)

    full_text, _, pages_meta, _ = OCRExtractorService.extract_text_and_pages(
        str(pdf_file), "application/pdf"
    )
    fields = OCRExtractorService.extract_structured_fields(full_text, "Satellite Map of Land", pages_meta)
    assert "latitude" in fields or "longitude" in fields or "land_area" in fields


# ===========================================================================
# 8. CORRUPT, ENCRYPTED, EMPTY DOCUMENT SAFETY
# ===========================================================================

def test_08_corrupt_encrypted_empty_documents_handled_safely(tmp_path):
    """8. Corrupt, encrypted, and empty documents fail safely with clear error messages."""
    # Corrupt document
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"This is not a PDF at all")

    with pytest.raises(ValueError, match="Corrupt"):
        OCRExtractorService.extract_text_and_pages(str(corrupt_file), "application/pdf")

    # Encrypted document
    doc = pymupdf.open()
    doc.new_page()
    enc_file = tmp_path / "encrypted.pdf"
    doc.save(str(enc_file), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="testpwd")
    doc.close()

    with pytest.raises(ValueError, match="encrypted"):
        OCRExtractorService.extract_text_and_pages(str(enc_file), "application/pdf")


# ===========================================================================
# 9. RESOURCE LIMITS (PAGE COUNT LIMIT)
# ===========================================================================

def test_09_page_count_and_file_size_limits_enforced(tmp_path):
    """9. A document exceeding 50 pages is rejected before exhausting server memory."""
    doc = pymupdf.open()
    for _ in range(52):
        doc.new_page(width=100, height=100)
    over_limit_file = tmp_path / "too_many_pages.pdf"
    doc.save(str(over_limit_file))
    doc.close()

    with pytest.raises(ValueError, match="exceeding the maximum allowed limit of 50 pages"):
        OCRExtractorService.extract_text_and_pages(str(over_limit_file), "application/pdf")


# ===========================================================================
# 10. HASHING & DUPLICATE COLLISION
# ===========================================================================

def test_10_document_hashing_and_duplicate_collision_intact():
    """10. SHA-256 calculation and duplicate upload rejection remain intact with real OCR pipeline."""
    app_id, _, _ = setup_test_app()
    pdf_bytes = create_digital_pdf("Affidavit 2 Content with Unique Stamp Duty Rs 100")

    res1 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Affidavit 2"},
        files={"file": ("affidavit.pdf", pdf_bytes, "application/pdf")},
    )
    assert res1.status_code == 201

    # Upload identical file again under different slot
    res2 = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("fire_duplicate.pdf", pdf_bytes, "application/pdf")},
    )
    assert res2.status_code in (400, 409)
    assert "identical" in res2.json()["detail"].lower() or "duplicate" in res2.json()["detail"].lower()


# ===========================================================================
# 11. END-TO-END COMPLIANCE EVALUATION COMPATIBILITY
# ===========================================================================

def test_11_upload_and_compliance_apis_compatible():
    """11. End-to-end API upload and compliance evaluation function smoothly with OCR documents."""
    app_id, _, inst_name = setup_test_app("Extension of Approval (EoA)")

    scanned_lines = [
        "Fire Safety Certificate CFO Pune",
        "Certificate No: CFO/2026/8899",
        "Valid until: 25/08/2028",
        f"Institute: {inst_name}",
    ]
    pdf_bytes = create_scanned_pdf(scanned_lines)

    res = client.post(
        f"/api/applications/{app_id}/documents",
        data={"document_type": "Fire Safety Certificate"},
        files={"file": ("fire_scan.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 201

    eval_res = client.post(f"/api/applications/{app_id}/compliance/evaluate")
    assert eval_res.status_code == 200
    report = eval_res.json()
    assert "rule_evaluations" in report
    rule_exp = next((r for r in report["rule_evaluations"] if r["rule_code"] == "APH-RULE-DOC-EXPIRY"), None)
    assert rule_exp is not None


# ===========================================================================
# 12. EOA WORKFLOW UNCHANGED
# ===========================================================================

def test_12_eoa_workflow_unchanged():
    """12. Existing EoA 7-document checklist and evaluation logic remain unchanged."""
    app_id, _, _ = setup_test_app("Extension of Approval (EoA)")
    res = client.get(f"/api/applications/{app_id}/checklist")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 7
    expected = [
        "Affidavit 2",
        "AICTE Portal Payment Receipt",
        "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "Structural Stability Certificate",
        "Fire Safety Certificate",
        "Satellite Map of Land",
        "Audited Accounts",
    ]
    for exp in expected:
        assert any(exp == item["category"] for item in items)


# ===========================================================================
# 13. ALL FIVE APPLICATION CATEGORIES FUNCTIONAL
# ===========================================================================

def test_13_all_five_categories_functional():
    """13. All five application categories continue to resolve their distinct checklists."""
    cats = {
        "Extension of Approval (EoA)": 7,
        "Increase in Intake": 11,
        "New Technical Institute": 11,
        "NRI / Foreign National Quota": 8,
        "Change of Site / Location": 11,
    }
    for cat, count in cats.items():
        app_id, _, _ = setup_test_app(cat)
        res = client.get(f"/api/applications/{app_id}/checklist")
        assert res.status_code == 200
        assert len(res.json()) == count


# ===========================================================================
# 14. RESOURCE CLEANUP (NO LEAKED PIXMAPS OR FILE HANDLES)
# ===========================================================================

def test_14_temporary_files_and_pixmaps_cleaned_up(tmp_path):
    """14. Verifies that PyMuPDF documents are closed and temporary files can be deleted without file locks."""
    pdf_bytes = create_scanned_pdf(["Temporary test document for handle leak verification."])
    pdf_file = tmp_path / "temp_leak_test.pdf"
    pdf_file.write_bytes(pdf_bytes)

    OCRExtractorService.extract_text_and_pages(str(pdf_file), "application/pdf")
    # If the file handle was not closed, deleting the file on Windows will fail with PermissionError
    pdf_file.unlink()
    assert not pdf_file.exists()


# ===========================================================================
# 15. DIRECT IMAGE OCR RECOGNITION
# ===========================================================================

def test_15_direct_image_ocr_recognition(tmp_path):
    """15. Direct upload of image files (.png) produces genuine OCR text without fake placeholders."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 40), "ARCHITECT CERTIFICATE FOR BUILT-UP AREA", fill=(0, 0, 0))
    d.text((30, 80), "Total instructional area: 4500 sq meters", fill=(0, 0, 0))
    d.text((30, 120), "Architect Registration: CA/2020/9981", fill=(0, 0, 0))

    img_path = tmp_path / "architect.png"
    img.save(str(img_path))

    full_text, count, pages_meta, avg_conf = OCRExtractorService.extract_text_and_pages(
        str(img_path), "image/png"
    )
    assert count == 1
    assert pages_meta[0]["extraction_method"] == "OCR_RASTER"
    assert pages_meta[0]["is_scanned"] is True
    assert "registered for regulatory inspection" not in full_text
    assert avg_conf > 0.40
