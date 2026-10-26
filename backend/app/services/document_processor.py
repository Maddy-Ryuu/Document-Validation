import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import (
    Document,
    DocumentExtraction,
    DocumentProcessingJob,
    AuditEvent,
)
from app.services.storage import get_storage_service
from app.services.ocr import OCRExtractorService

logger = logging.getLogger(__name__)


def process_document_sync(db: Session, document_id: str) -> Document:
    """
    Executes document extraction, OCR rasterization, field parsing and saves results.
    Can be run synchronously or wrapped inside background tasks.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document with ID {document_id} not found")

    # Update state to Processing
    doc.processing_status = "Processing"
    doc.processing_error = None
    job = DocumentProcessingJob(
        document_id=doc.id,
        status="PROCESSING",
        started_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()

    storage_service = get_storage_service()

    try:
        file_path = storage_service.get_file_path(doc.private_storage_key)

        # 1. Integrity check
        if doc.sha256_hash:
            if not storage_service.verify_integrity(doc.private_storage_key, doc.sha256_hash):
                raise ValueError("SHA-256 integrity verification failed: file content mismatch on disk")

        # 2. Extract text & pages
        raw_text, page_count, pages_metadata, avg_conf = OCRExtractorService.extract_text_and_pages(
            file_path=file_path,
            mime_type=doc.detected_mime_type or "application/pdf"
        )

        # 3. Extract structured regulatory fields
        structured_fields = OCRExtractorService.extract_structured_fields(
            text=raw_text,
            document_type=doc.document_type,
            pages_metadata=pages_metadata
        )

        warnings = []
        if avg_conf < 0.60:
            warnings.append("Low overall OCR confidence score; visual human inspection recommended.")
        if not structured_fields:
            warnings.append("No standard regulatory fields could be automatically matched in this document.")

        # 4. Save DocumentExtraction
        extraction = DocumentExtraction(
            document_id=doc.id,
            raw_text=raw_text,
            page_count=page_count,
            structured_fields=structured_fields,
            confidence_score=avg_conf,
            extraction_engine="PyMuPDF + EasyOCR",
            extraction_status="SUCCESS" if structured_fields else "PARTIAL",
            warnings=warnings,
        )
        db.add(extraction)

        # Update Document status
        doc.processing_status = "Processed" if not warnings else "Needs Review"
        doc.updated_at = datetime.utcnow()

        # Update Job
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()

        # Audit Event
        audit = AuditEvent(
            entity_type="Document",
            entity_id=doc.id,
            action="OCR_PROCESS",
            details={
                "page_count": page_count,
                "confidence": avg_conf,
                "fields_extracted": list(structured_fields.keys()),
                "status": doc.processing_status
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)
        return doc

    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}", exc_info=True)
        doc.processing_status = "Failed"
        doc.processing_error = str(e)
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()

        audit = AuditEvent(
            entity_type="Document",
            entity_id=doc.id,
            action="OCR_PROCESS_FAILED",
            details={"error": str(e)}
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)
        return doc
