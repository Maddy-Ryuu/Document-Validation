# AICTE Application Validation & Compliance Verification Platform
## Phase 2 — Document Upload, Secure Storage, OCR & Information Extraction

**Problem Statement ID:** 26261  
**Project Title:** AI-Powered Application Validation, Document Authentication and Regulatory Compliance Verification

---

## 1. Overview & Architecture

Phase 2 extends the platform with end-to-end regulatory document handling, secure private storage, SHA-256 integrity auditing, digital and scanned OCR extraction (PyMuPDF & EasyOCR/rasterization), side-by-side inspection, officer correction auditing, traceable version replacement, and dynamic Approval Process Handbook (APH 2026-27) checklist validation.

---

## 2. Key Components Implemented in Phase 2

### A. Storage Abstraction Layer (`backend/app/services/storage.py`)
- Pluggable storage architecture (`StorageService`, `LocalStorageService`, and expandable to `S3StorageService`).
- Files stored securely outside the public web root (`storage/documents/`).
- Unique UUID-based storage keys prevent directory traversal and filename collision vulnerabilities.
- Cryptographic SHA-256 hash calculated during stream consumption and stored in metadata.
- On-demand recalculation verifies file integrity against disk tampering.

### B. OCR & Information Extraction Pipeline (`backend/app/services/ocr.py`)
- **PyMuPDF:** Multi-page digital text vector extraction preserving page boundaries and character counts.
- **Scanned Page Detection:** Automatically flags sparse or scanned pages for image rasterization and OCR processing.
- **Regulatory Field Extraction:** Extracts key regulatory fields with page numbers, confidence metrics, and verbatim evidence snippets:
  - Institution Name
  - Certificate / Sanction Number
  - Issue Date & Validity / Expiry Date
  - Issuing Competent Authority (e.g., Director General Fire Services, Sub-Registrar)
  - Survey / Khasra Land Number, Land Area and Units
  - Built-up Instructional Area (sqm)

### C. Officer Correction & Replacement Auditing
- Scrutiny officers can correct OCR-extracted values directly in the UI.
- All field corrections preserve the original OCR value, timestamp, correcting officer reference, and audit reason in `document_corrections`.
- Replaced documents are version-incremented (`v1` -> `v2`) and linked via `replaces_document_id` without deleting historical versions.

### D. Approval Process Handbook (APH) Checklist (`backend/app/services/checklist.py`)
- Configured document requirements mapped to application category and academic year.
- Differentiates Mandatory vs. Optional regulatory categories.
- Real-time status mapping (`Not uploaded`, `Uploaded`, `Queued`, `Processing`, `Processed`, `Needs Review`, `Failed`).

### E. Frontend Document Workspace & Side-by-Side Review
- **Document Checklist View:** Live status badges, upload triggers, and inspection shortcuts.
- **Upload Modal:** Drag-and-drop file upload supporting PDF, PNG, JPG up to 25 MB with frontend & backend validation.
- **Side-by-Side Document Viewer:**
  - Left pane: Original embedded PDF / image preview with SHA-256 integrity hash verification footer.
  - Right pane: Structured regulatory fields, confidence percentages, evidence snippets, officer correction interface, raw OCR text tab, and version lineage tab.

---

## 3. Database Changes (Alembic Migration: `6923ff566fc0`)

- **New Tables:**
  - `document_extractions`: Raw OCR text, page count, structured JSON fields, confidence score, warnings, and extraction engine.
  - `document_corrections`: Immutable log of officer modifications to extracted fields.
  - `document_processing_jobs`: Background task tracking, status, and error logs.
- **Extended Columns on `documents`:**
  - `detected_mime_type`, `file_size_bytes`, `version`, `replaces_document_id`, `uploaded_by_user_id`, `processing_error`.

---

## 4. REST API Endpoints (Phase 2)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/applications/{id}/documents` | Upload file, compute SHA-256, store in private storage, queue OCR |
| `GET` | `/api/applications/{id}/documents` | Paginated listing of documents for an application |
| `GET` | `/api/documents/{id}` | Return document metadata and status |
| `GET` | `/api/documents/{id}/file` | Stream original file with integrity check |
| `GET` | `/api/documents/{id}/extraction` | Get extracted text, structured fields, confidence, and page references |
| `POST` | `/api/documents/{id}/process` | Trigger / retry OCR extraction |
| `PATCH` | `/api/documents/{id}/extraction` | Save officer corrections with audit history |
| `GET` | `/api/applications/{id}/checklist` | APH document checklist with upload statuses |
| `GET` | `/api/documents/{id}/versions` | Get replacement and version lineage |

---

## 5. Startup Commands

### Backend:
```bash
cd backend
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation: [http://localhost:8000/docs](http://localhost:8000/docs).

### Frontend:
```bash
cd frontend
npm run dev
```
Platform interface: [http://localhost:5173](http://localhost:5173).

---

## 6. Automated Test Suite Results

Run complete test suite:
```bash
cd backend
python -m pytest tests/ -v
```

**Results:**
- `tests/test_api.py`: 6 passed (Phase 1 health check, dashboard KPIs, institution CRUD, duplicate protection, application lifecycle).
- `tests/test_documents.py`: 7 passed (APH checklist, PDF upload & text extraction, field correction audit, version replacement, duplicate rejection, format validation, regression).
- **Total:** 13 passed in 2.81s.
