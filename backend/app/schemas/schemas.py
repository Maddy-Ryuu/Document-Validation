from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class InstitutionCreate(InstitutionBase):
    pass


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
