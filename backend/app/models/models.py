import uuid
import re
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Text,
    JSON,
    LargeBinary,
    Index,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def normalize_institution_field(val: Optional[str]) -> str:
    """Normalizes institution fields: trims whitespace, collapses internal spaces, and lowercases."""
    if not val:
        return ""
    return re.sub(r"\s+", " ", val.strip()).lower()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="reviewer")  # admin, reviewer, compliance_officer
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    applications = relationship("Application", back_populates="assigned_reviewer")
    review_actions = relationship("ReviewAction", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    uploaded_documents = relationship("Document", back_populates="uploaded_by_user")
    corrections = relationship("DocumentCorrection", back_populates="user")


class Institution(Base):
    __tablename__ = "institutions"
    __table_args__ = (
        UniqueConstraint("normalized_name", "normalized_city", "normalized_state", name="uq_institutions_normalized_location"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_identifier = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    institution_type = Column(String(100), nullable=False)  # Engineering, Management, Pharmacy, Polytechnic
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    normalized_city = Column(String(100), nullable=False, index=True)
    normalized_state = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")


@event.listens_for(Institution, "before_insert")
def populate_normalized_fields_before_insert(mapper, connection, target):
    target.normalized_name = normalize_institution_field(target.name)
    target.normalized_city = normalize_institution_field(target.city)
    target.normalized_state = normalize_institution_field(target.state)


@event.listens_for(Institution, "before_update")
def populate_normalized_fields_before_update(mapper, connection, target):
    if target.name:
        target.normalized_name = normalize_institution_field(target.name)
    if target.city:
        target.normalized_city = normalize_institution_field(target.city)
    if target.state:
        target.normalized_state = normalize_institution_field(target.state)


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_identifier = Column(String(100), unique=True, nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_category = Column(String(100), nullable=False)  # Extension of Approval (EoA), New Institute, Increase in Intake, NRI Quota
    academic_year = Column(String(20), nullable=False)  # 2026-2027
    status = Column(String(50), nullable=False, default="Under Validation", index=True)  # Submitted, Under Validation, Action Required, Verified, Approved, Rejected
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    institution = relationship("Institution", back_populates="applications")
    assigned_reviewer = relationship("User", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    validation_runs = relationship("ValidationRun", back_populates="application", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="application", cascade="all, delete-orphan")
    verification_checks = relationship("VerificationCheck", back_populates="application", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="application", cascade="all, delete-orphan")
    review_actions = relationship("ReviewAction", back_populates="application", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False)  # Category e.g. Land Title Certificate, Fire Safety NOC
    original_filename = Column(String(255), nullable=False)
    private_storage_key = Column(String(500), nullable=True)
    detected_mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    replaces_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processing_status = Column(String(50), nullable=False, default="Uploaded")  # Uploaded, Queued, Processing, Processed, Needs Review, Failed
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")
    extractions = relationship("DocumentExtraction", back_populates="document", cascade="all, delete-orphan")
    corrections = relationship("DocumentCorrection", back_populates="document", cascade="all, delete-orphan")
    processing_jobs = relationship("DocumentProcessingJob", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="document")
    verification_checks = relationship("VerificationCheck", back_populates="document")
    replaced_by = relationship("Document", remote_side=[id])


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    page_count = Column(Integer, default=1, nullable=False)
    structured_fields = Column(JSON, nullable=True)  # {field_name: {value, page, confidence, source_snippet}}
    confidence_score = Column(Float, nullable=True)  # Overall OCR & Extraction confidence 0.0 - 1.0
    extraction_engine = Column(String(100), default="PyMuPDF+EasyOCR", nullable=False)
    extraction_status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, PARTIAL, FAILED
    warnings = Column(JSON, nullable=True)  # List of warnings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="extractions")


class DocumentCorrection(Base):
    __tablename__ = "document_corrections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="corrections")
    user = relationship("User", back_populates="corrections")


class DocumentProcessingJob(Base):
    __tablename__ = "document_processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED
    attempt_count = Column(Integer, default=1, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="processing_jobs")


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    document_type = Column(String(100), nullable=True)
    application_category = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False, default="Medium")  # Low, Medium, High, Critical
    weight = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="Running")  # Running, Completed, Failed
    progress = Column(Integer, default=0, nullable=False)  # 0 to 100
    rule_version_reference = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    application = relationship("Application", back_populates="validation_runs")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    validation_run_id = Column(String(36), ForeignKey("validation_runs.id", ondelete="SET NULL"), nullable=True)
    rule_code = Column(String(50), nullable=True)
    category = Column(String(100), nullable=False)  # Regulatory, Document Discrepancy, Land Norms, Faculty Ratio
    severity = Column(String(20), nullable=False, default="Medium")  # Low, Medium, High, Critical
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_reference = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="Open")  # Open, Resolved, Ignored
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="findings")
    document = relationship("Document", back_populates="findings")
    review_actions = relationship("ReviewAction", back_populates="finding")


class VerificationCheck(Base):
    __tablename__ = "verification_checks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_name = Column(String(100), nullable=False)  # e.g., Land Revenue Dept, Municipal Corp, Fire Service, AICTE Central DB
    source_reference = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="Pending")  # Pending, In Progress, Verified, Failed
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    result_summary = Column(Text, nullable=True)

    application = relationship("Application", back_populates="verification_checks")
    document = relationship("Document", back_populates="verification_checks")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    assessment_level = Column(String(50), nullable=False, default="Application")  # Application, Document
    score = Column(Float, nullable=True)  # 0.0 - 100.0
    risk_band = Column(String(20), nullable=True)  # Low, Medium, High, Extreme
    factor_breakdown = Column(JSON, nullable=True)
    evidence_coverage = Column(Float, nullable=True)  # Percentage 0.0 - 100.0
    assessment_version = Column(String(50), default="1.0", nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="risk_assessments")


class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)  # Approved, Rejected, Clarification Requested, Finding Resolved
    comments = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    application = relationship("Application", back_populates="review_actions")
    finding = relationship("Finding", back_populates="review_actions")
    user = relationship("User", back_populates="review_actions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(100), nullable=False)  # Application, Institution, Document, ValidationRule
    entity_id = Column(String(36), nullable=False)
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, UPLOAD, OCR_PROCESS, CORRECTION, REPLACEMENT, INTEGRITY_CHECK
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default="INFO")  # INFO, WARNING, ALERT, SUCCESS
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class DocumentBlob(Base):
    __tablename__ = "document_blobs"

    storage_key = Column(String(500), primary_key=True)
    file_data = Column(LargeBinary, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
