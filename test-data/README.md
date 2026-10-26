# Synthetic Document Test Pack (Phase 2)
## AICTE Application Validation & Compliance Verification Platform

This directory contains a complete synthetic PDF test suite created specifically for Phase 2 benchmarking and automated testing of the AICTE Application Validation platform.

> **CRITICAL COMPLIANCE NOTICE:**  
> Every document in this pack is marked:  
> `SYNTHETIC TEST DOCUMENT — NOT AN OFFICIAL RECORD`  
> All institution names, individual names, registration numbers, and addresses are completely fictional. These documents are never automatically seeded into the operational production database.

---

## 1. Directory Structure

```
test-data/
├── manifest.json                                # Machine-readable test manifest with expected fields & hashes
├── README.md                                    # This test documentation and usage guide
├── standard-pack/                               # 7 Core AICTE Dossier Documents (All PASS)
│   ├── 01_institution_profile.pdf
│   ├── 02_previous_eoa_record.pdf
│   ├── 03_affidavit_undertaking.pdf
│   ├── 04_noc_fire_safety.pdf
│   ├── 05_accreditation_certificate.pdf
│   ├── 06_faculty_qualification_records.pdf
│   └── 07_payment_receipt.pdf
└── variants/                                    # Edge Cases & Validation Stress Test Variants
    ├── variant_expired_certificate.pdf          # Expired validity date (Expected: FAIL / Discrepancy)
    ├── variant_missing_required_field.pdf       # Missing mandatory principal field (Expected: FLAG_FOR_REVIEW)
    ├── variant_cross_doc_mismatch.pdf           # Different institution ID & name (Expected: FAIL / Cross Mismatch)
    ├── variant_exact_duplicate.pdf              # Exact SHA-256 duplicate of receipt (Expected: REJECT / Duplicate)
    └── variant_scanned_ocr_test.pdf             # Raster image PDF without text stream (Expected: PASS_VIA_OCR)
```

---

## 2. Standard Document Pack (7 Documents)

| # | File Name | Document Type | Description | Target Fields | Intended Outcome |
|---|---|---|---|---|---|
| 1 | `01_institution_profile.pdf` | Institution Profile & Land Dossier | Details campus acreage (5.25 Acres), survey numbers, built-up area (14,850 sqm), and society registration. | `institution_name`, `institution_identifier`, `land_area`, `survey_number`, `built_up_area_sqm` | **PASS** |
| 2 | `02_previous_eoa_record.pdf` | Extension of Approval (EoA) | Prior year approval letter from Western Regional Office with active courses & sanctioned intake. | `certificate_number`, `issue_date`, `valid_until`, `approved_programs` | **PASS** |
| 3 | `03_affidavit_undertaking.pdf` | Sworn Legal Undertaking | Notarized Form-A affidavit on e-Stamp paper confirming accuracy and infrastructure availability. | `affidavit_reference`, `deponent_name`, `notary_authority`, `attestation_date` | **PASS** |
| 4 | `04_noc_fire_safety.pdf` | Fire Safety NOC | Valid PMRDA Chief Fire Officer NOC with inspection findings through 15-05-2027. | `certificate_number`, `issuing_authority`, `valid_until`, `survey_number` | **PASS** |
| 5 | `05_accreditation_certificate.pdf` | NAAC Accreditation Certificate | Valid Institutional Grade A+ certificate (CGPA 3.42) through September 2028. | `certificate_number`, `grade`, `cgpa`, `valid_until`, `issuing_authority` | **PASS** |
| 6 | `06_faculty_qualification_records.pdf` | Faculty Qualification & Cadre Roster | Cadre breakdown, Ph.D. density (41.2%), and list of department heads with Dr. Arvind R. Kulkarni. | `principal_director_name`, `total_faculty_count`, `phd_faculty_count`, `cadre_ratio_declared` | **PASS** |
| 7 | `07_payment_receipt.pdf` | Payment Voucher / Challan | Official Bharatkosh/SBI payment voucher confirming INR 3,50,000 regulatory scrutiny fee payment. | `transaction_reference`, `challan_number`, `amount_inr`, `transaction_status` | **PASS** |

---

## 3. Test Variants (Edge Cases)

| Variant File | Intended Finding & Failure Mode | Intended Outcome | Expected Rule Code |
|---|---|---|---|
| `variant_expired_certificate.pdf` | Fire safety NOC with validity `15-05-2023`, which is expired for AY 2026-27. | **FAIL** | `APH-RULE-DOC-EXPIRY` |
| `variant_missing_required_field.pdf` | Faculty roster where `Principal / Director Name` line has been stripped. | **FLAG_FOR_REVIEW** | `APH-RULE-FAC-PRINCIPAL` |
| `variant_cross_doc_mismatch.pdf` | EoA issued to `Zenith Polytechnic & Technology Campus` (`1-9999999999`) instead of Apex. | **FAIL** | `APH-RULE-CROSS-ID-MISMATCH` |
| `variant_exact_duplicate.pdf` | Exact duplicate of `07_payment_receipt.pdf` with identical SHA-256 hash. | **REJECT / FLAG** | `APH-RULE-DUP-HASH` |
| `variant_scanned_ocr_test.pdf` | High-resolution rasterized scan with 0 text characters, testing OCR fallback. | **PASS_VIA_OCR** | `APH-INFO-SCANNED-DOC` |

---

## 4. How to Test Through the Application

### Option A: Via the Web Dashboard (Interactive UI)
1. **Start Backend & Frontend Services:**
   - In terminal 1 (backend):
     ```bash
     cd backend
     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
     ```
   - In terminal 2 (frontend):
     ```bash
     cd frontend
     npm run dev
     ```
2. Open the web browser at `http://localhost:5173`.
3. Navigate to **Applications** and open any application dossier (or create a new application for Apex Institute).
4. Drag and drop any test PDF from `test-data/standard-pack/` or `test-data/variants/` into the upload dropzone.
5. Observe the processing pipeline:
   - SHA-256 hashing and integrity check.
   - OCR / PyMuPDF text and page extraction.
   - Structured field extraction card displaying confidence scores and page references.
   - Findings raised if uploading one of the variants (e.g. Expired Certificate or Mismatch).

### Option B: Via Python Test Runner or Pytest
Run the test runner against the OCR service directly:
```bash
python -c "
from app.services.ocr import OCRExtractorService
text, pages, meta, conf = OCRExtractorService.extract_text_and_pages('test-data/standard-pack/04_noc_fire_safety.pdf', 'application/pdf')
fields = OCRExtractorService.extract_structured_fields(text, 'Fire Safety NOC', meta)
print('OCR Confidence:', conf)
print('Extracted Fields:', fields)
"
```
