from datetime import datetime
from typing import Optional, List, Dict, Any
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# User Schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    role: str = "reviewer"
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Institution Schemas
class InstitutionBase(BaseModel):
    institution_identifier: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=3, max_length=255)
    institution_type: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)

    @field_validator("institution_identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Institution identifier cannot be empty")
        return cleaned

    @field_validator("name", "city", "state")
    @classmethod
    def validate_strings(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", " ", v.strip())
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace only")
        return cleaned


class InstitutionCreate(InstitutionBase):
    pass


class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    institution_type: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    institution_identifier: Optional[str] = Field(None, min_length=2, max_length=100)

    @field_validator("institution_identifier")
    @classmethod
    def validate_identifier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().upper()
            if not cleaned:
                raise ValueError("Institution identifier cannot be empty")
            return cleaned
        return v

    @field_validator("name", "city", "state")
    @classmethod
    def validate_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = re.sub(r"\s+", " ", v.strip())
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace only")
            return cleaned
        return v


class InstitutionResponse(InstitutionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    application_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    application_id: str
    document_type: str
    original_filename: str
    file_size_bytes: Optional[int] = None
    detected_mime_type: Optional[str] = None
    sha256_hash: Optional[str] = None
    version: int = 1
    replaces_document_id: Optional[str] = None
    processing_status: str
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentExtractionResponse(BaseModel):
    id: str
    document_id: str
    raw_text: Optional[str] = None
    page_count: int
    structured_fields: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    extraction_engine: str
    extraction_status: str
    warnings: Optional[List[str]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentCorrectionCreate(BaseModel):
    field_name: str
    corrected_value: str
    reason: Optional[str] = None


class DocumentCorrectionResponse(BaseModel):
    id: str
    document_id: str
    field_name: str
    original_value: Optional[str] = None
    corrected_value: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChecklistItem(BaseModel):
    category: str
    description: str
    criticality: str
    is_mandatory: bool
    is_conditional: bool = False
    condition_description: Optional[str] = None
    regulatory_source: Optional[Dict[str, Any]] = None
    is_source_unconfirmed: bool = False
    status: str  # Not uploaded, Uploaded, Queued, Processing, Processed, Needs Review, Failed
    uploaded_document: Optional[DocumentResponse] = None


# Application Schemas
class ApplicationBase(BaseModel):
    institution_id: str
    application_category: str = Field(..., min_length=2, max_length=100)
    academic_year: str = Field(..., min_length=4, max_length=20)
    application_identifier: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    assigned_reviewer_id: Optional[str] = None
    application_category: Optional[str] = None
    academic_year: Optional[str] = None


class FindingResponse(BaseModel):
    id: str
    application_id: str
    category: str
    severity: str
    title: str
    explanation: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskFactorItem(BaseModel):
    factor_code: str
    factor_name: str
    points: int
    rule_code: Optional[str] = None
    finding_id: Optional[str] = None
    evidence_reference: Optional[str] = None
    reason: str
    severity: str


class RiskAssessmentReportResponse(BaseModel):
    id: str
    application_id: str
    application_identifier: str
    validation_run_id: Optional[str] = None
    score: float
    risk_band: str
    completeness_status: str
    evidence_coverage: Optional[float] = None
    is_provisional: bool
    explanation: str
    assessment_version: str
    contributing_factors: List[RiskFactorItem] = []
    missing_evidence_items: List[str] = []
    unresolved_reviews: List[str] = []
    calculated_at: datetime


class RiskConfigResponse(BaseModel):
    version: str
    weights: Dict[str, int]
    bands: Dict[str, Dict[str, Any]]
    completeness_states: List[str]


class RiskAssessmentResponse(BaseModel):
    id: str
    application_id: str
    assessment_level: str
    score: Optional[float] = None
    risk_band: Optional[str] = None
    factor_breakdown: Optional[Dict[str, Any]] = None
    evidence_coverage: Optional[float] = None
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    id: str
    application_identifier: str
    institution_id: str
    institution_name: Optional[str] = None
    institution_type: Optional[str] = None
    institution_state: Optional[str] = None
    institution_city: Optional[str] = None
    application_category: str
    academic_year: str
    status: str
    submission_date: datetime
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []
    findings: List[FindingResponse] = []
    risk_assessments: List[RiskAssessmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ApplicationListItem(BaseModel):
    id: str
    application_identifier: str
    institution_id: str
    institution_name: str
    institution_state: str
    institution_city: str
    application_category: str
    academic_year: str
    status: str
    submission_date: datetime
    created_at: datetime
    documents_count: int = 0
    findings_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# Dashboard Schemas
class DashboardSummaryResponse(BaseModel):
    total_applications: int
    in_validation: int
    action_required: int
    verified_documents: int
    status_breakdown: Dict[str, int]
    risk_breakdown: Optional[Dict[str, int]] = None


class TrendPoint(BaseModel):
    date: str
    applications: int
    verified: int


class DashboardTrendsResponse(BaseModel):
    trends: List[TrendPoint]


# Generic Paginated Response
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int


# ===========================================================================
# PHASE 2: AUTHORITATIVE REFERENCE DATA SCHEMAS
# ===========================================================================

class ApprovedProgrammeSchema(BaseModel):
    id: str
    programme_name: str
    course_name: str
    level: str
    approved_intake: int
    nri_quota_approved: bool
    nri_quota_intake: int
    pio_fn_quota_approved: bool
    pio_fn_quota_intake: int
    accreditation_status: str
    accreditation_valid_until: Optional[datetime] = None
    academic_year: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class InstitutionApprovalHistorySchema(BaseModel):
    id: str
    academic_year: str
    eoa_application_number: Optional[str] = None
    eoa_issue_date: Optional[datetime] = None
    effective_start_date: datetime
    effective_end_date: datetime
    total_sanctioned_intake: int
    approval_type: str
    issuing_authority: str
    is_latest: bool

    model_config = ConfigDict(from_attributes=True)


class InstitutionReferenceResponse(BaseModel):
    id: str
    aicte_permanent_id: str
    legal_name: str
    institution_type: str
    state: str
    district_or_city: str
    address: Optional[str] = None
    standing_status: str
    established_year: Optional[int] = None
    initial_approval_year: Optional[int] = None
    latest_approval_year: Optional[int] = None
    verification_status: str
    source_provenance: str
    source_document_ref: Optional[str] = None
    data_freshness_date: datetime
    is_official: bool
    created_at: datetime
    approved_programmes: List[ApprovedProgrammeSchema] = []
    approval_history: List[InstitutionApprovalHistorySchema] = []

    model_config = ConfigDict(from_attributes=True)


class ReferenceMatchFieldResult(BaseModel):
    submitted_value: Optional[str]
    official_value: Optional[str]
    match: bool
    confidence: float
    notes: Optional[str] = None


class ReferenceMatchFinding(BaseModel):
    finding_type: str
    severity: str
    message: str
    reference_source: str
    effective_date: Optional[str] = None


class ReferenceMatchReportResponse(BaseModel):
    application_id: str
    institution_id: str
    reference_matched: bool
    institution_reference_id: Optional[str] = None
    aicte_permanent_id: Optional[str] = None
    legal_name: Optional[str] = None
    verification_status: str
    source_provenance: Optional[str] = None
    data_freshness_date: Optional[datetime] = None
    is_official: bool
    standing_status: Optional[str] = None
    matched_fields: Dict[str, ReferenceMatchFieldResult]
    findings: List[ReferenceMatchFinding]
    programmes_summary: List[ApprovedProgrammeSchema] = []
    latest_approval: Optional[InstitutionApprovalHistorySchema] = None
    recommendation: str
