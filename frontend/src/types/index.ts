export interface Institution {
  id: string;
  institution_identifier: string;
  name: string;
  institution_type: string;
  state: string;
  city: string;
  created_at: string;
  updated_at: string;
  application_count?: number;
}

export interface DocumentItem {
  id: string;
  application_id: string;
  document_type: string;
  original_filename: string;
  file_size_bytes?: number;
  detected_mime_type?: string;
  sha256_hash?: string;
  version: number;
  replaces_document_id?: string | null;
  processing_status: "Uploaded" | "Queued" | "Processing" | "Processed" | "Needs Review" | "Failed" | string;
  processing_error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentFieldExtraction {
  value: string;
  page?: number;
  confidence?: number;
  source_snippet?: string;
  corrected?: boolean;
  original_extracted_value?: string;
  correction_reason?: string;
}

export interface DocumentExtraction {
  id: string;
  document_id: string;
  raw_text?: string;
  page_count: number;
  structured_fields?: Record<string, DocumentFieldExtraction>;
  confidence_score?: number;
  extraction_engine: string;
  extraction_status: string;
  warnings?: string[];
  created_at: string;
}

export interface ChecklistItem {
  category: string;
  description: string;
  criticality: "Mandatory" | "Required" | "Optional" | "Conditional" | string;
  is_mandatory: boolean;
  is_conditional?: boolean;
  condition_description?: string | null;
  regulatory_source?: RegulatorySource | null;
  is_source_unconfirmed?: boolean;
  status: "Not uploaded" | "Uploaded" | "Queued" | "Processing" | "Processed" | "Needs Review" | "Failed" | string;
  uploaded_document?: DocumentItem | null;
}

export interface RegulatorySource {
  title: string;
  section: string;
  page?: string;
  applicable_academic_year?: string;
  source_url?: string;
}

export interface RegulatoryRule {
  rule_code: string;
  rule_version: string;
  rule_type: "OFFICIAL_REGULATORY" | "TECHNICAL_CHECK" | "PENDING_CONFIRMATION" | string;
  name: string;
  category: string;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  description: string;
  regulatory_source: RegulatorySource;
  target_document_type?: string | null;
  condition: string;
  threshold?: any;
}

export interface RuleEvaluationResult {
  rule_code: string;
  rule_name: string;
  result: "PASS" | "FAIL" | "NEEDS_REVIEW" | "NOT_EVALUATED" | "NOT_APPLICABLE" | string;
  severity: string;
  explanation: string;
  regulatory_source: RegulatorySource;
  actual_value?: any;
  expected_value?: any;
  missing_items?: string[];
  mismatches?: Array<{ file: string; found: string }>;
  is_pending_confirmation?: boolean;
}

export interface ComplianceEvaluationReport {
  validation_run_id: string;
  application_id: string;
  application_identifier: string;
  compliance_status: string;
  summary: {
    passed: number;
    failed: number;
    needs_review: number;
    not_evaluated?: number;
    not_applicable?: number;
    total_evaluated: number;
  };
  rule_evaluations: RuleEvaluationResult[];
  findings_count: number;
}

export interface FindingItem {
  id: string;
  application_id: string;
  document_id?: string | null;
  rule_code?: string | null;
  category: string;
  severity: "Low" | "Medium" | "High" | "Critical" | string;
  title: string;
  explanation: string;
  evidence_reference?: string | null;
  status: string;
  created_at: string;
}

export interface RiskAssessmentItem {
  id: string;
  application_id: string;
  assessment_level: string;
  score: number | null;
  risk_band: "Low" | "Medium" | "High" | "Extreme" | null;
  factor_breakdown: Record<string, any> | null;
  evidence_coverage: number | null;
  calculated_at: string;
}

export interface ApplicationListItem {
  id: string;
  application_identifier: string;
  institution_id: string;
  institution_name: string;
  institution_state: string;
  institution_city: string;
  application_category: string;
  academic_year: string;
  status: "Under Validation" | "Action Required" | "Verified" | "Approved" | "Rejected" | string;
  submission_date: string;
  created_at: string;
  documents_count: number;
  findings_count: number;
}

export interface ApplicationDetail extends ApplicationListItem {
  institution_type?: string;
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  updated_at: string;
  documents: DocumentItem[];
  findings: FindingItem[];
  risk_assessments: RiskAssessmentItem[];
}

export interface RiskFactorItem {
  factor_code: string;
  factor_name: string;
  points: number;
  rule_code?: string;
  finding_id?: string;
  evidence_reference?: string;
  reason: string;
  severity: string;
}

export interface RiskAssessmentReport {
  id: string;
  application_id: string;
  application_identifier: string;
  validation_run_id?: string;
  score: number;
  risk_band: "Low" | "Medium" | "High" | string;
  completeness_status: "COMPLETE" | "INCOMPLETE" | "REQUIRES_REVIEW" | string;
  evidence_coverage?: number;
  is_provisional: boolean;
  explanation: string;
  assessment_version: string;
  contributing_factors: RiskFactorItem[];
  missing_evidence_items: string[];
  unresolved_reviews: string[];
  calculated_at: string;
  history?: Array<{
    id: string;
    score: number;
    risk_band: string;
    completeness_status: string;
    calculated_at: string;
    factors_count: number;
  }>;
}

export interface RiskConfig {
  version: string;
  weights: Record<string, number>;
  bands: Record<string, { min: number; max: number; label: string }>;
  completeness_states: string[];
}

export interface DashboardSummary {
  total_applications: number;
  in_validation: number;
  action_required: number;
  verified_documents: number;
  status_breakdown: Record<string, number>;
  risk_breakdown?: Record<string, number>;
}

export interface TrendPoint {
  date: string;
  applications: number;
  verified: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface CreateApplicationPayload {
  institution_id: string;
  application_category: string;
  academic_year: string;
  application_identifier?: string;
}

export interface CreateInstitutionPayload {
  institution_identifier: string;
  name: string;
  institution_type: string;
  state: string;
  city: string;
}

export interface DocumentReviewItem extends DocumentItem {
  application_identifier?: string;
  institution_id?: string;
  institution_name?: string;
  confidence_score?: number | null;
  extraction_status?: string | null;
  structured_fields?: Record<string, DocumentFieldExtraction> | null;
  findings_count?: number;
}

export interface QueueItem {
  id: string;
  application_identifier: string;
  institution_id: string;
  institution_name?: string;
  institution_city?: string;
  institution_state?: string;
  application_category: string;
  academic_year: string;
  status: string;
  submission_date: string;
  created_at: string;
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  risk_band?: string;
  risk_score?: number | null;
  priority: "High" | "Medium" | "Low";
  documents_count: number;
  findings_count: number;
}

export interface AuditEventItem {
  id: string;
  user_id?: string | null;
  entity_type: string;
  entity_id: string;
  action: string;
  details: Record<string, any>;
  created_at: string;
}

export interface AnalyticsReport {
  total_applications: number;
  total_institutions: number;
  total_documents: number;
  total_findings: number;
  status_breakdown: Record<string, number>;
  category_breakdown: Record<string, number>;
  institution_type_breakdown: Record<string, number>;
  risk_breakdown: Record<string, number>;
  findings_by_severity: Record<string, number>;
  document_status_breakdown: Record<string, number>;
  state_distribution: Record<string, number>;
  recent_activity: AuditEventItem[];
}

export interface SystemSettings {
  system: {
    project_name: string;
    environment: string;
    version: string;
    handbook_edition: string;
    storage_type: string;
    database_engine: string;
    database_connected: boolean;
    total_persisted_applications: number;
    total_persisted_institutions: number;
  };
  officer_profile: {
    name: string;
    designation: string;
    bureau: string;
    email: string;
    assigned_region: string;
    role: string;
    permissions: string[];
  };
  security_status: {
    document_authorization: string;
    integrity_checks: string;
    audit_immutability: string;
    sso_two_factor: string;
    biometric_auth: string;
  };
}


// ===========================================================================
// PHASE 2: AUTHORITATIVE REFERENCE DATA & CROSS-VERIFICATION TYPES
// ===========================================================================

export interface ApprovedProgrammeReference {
  id: string;
  programme_name: string;
  course_name: string;
  level: string;
  approved_intake: number;
  nri_quota_approved: boolean;
  nri_quota_intake: number;
  pio_fn_quota_approved: boolean;
  pio_fn_quota_intake: number;
  accreditation_status: string;
  accreditation_valid_until?: string | null;
  academic_year: string;
  is_active: boolean;
}

export interface InstitutionApprovalHistoryReference {
  id: string;
  academic_year: string;
  eoa_application_number?: string | null;
  eoa_issue_date?: string | null;
  effective_start_date: string;
  effective_end_date: string;
  total_sanctioned_intake: number;
  approval_type: string;
  issuing_authority: string;
  is_latest: boolean;
}

export interface InstitutionReferenceRecord {
  id: string;
  aicte_permanent_id: string;
  legal_name: string;
  institution_type: string;
  state: string;
  district_or_city: string;
  address?: string | null;
  standing_status: "APPROVED_IN_GOOD_STANDING" | "DEFICIENT" | "WITHDRAWN_OR_REVOKED" | string;
  established_year?: number | null;
  initial_approval_year?: number | null;
  latest_approval_year?: number | null;
  verification_status: "OFFICIAL_VERIFIED" | "PROVISIONAL_PENDING" | "SYNTHETIC_BENCHMARK" | "UNVERIFIED" | string;
  source_provenance: string;
  source_document_ref?: string | null;
  data_freshness_date: string;
  is_official: boolean;
  created_at: string;
  approved_programmes: ApprovedProgrammeReference[];
  approval_history: InstitutionApprovalHistoryReference[];
}

export interface ReferenceMatchFieldResult {
  submitted_value?: string | null;
  official_value?: string | null;
  match: boolean;
  confidence: number;
  notes?: string | null;
}

export interface ReferenceMatchFinding {
  finding_type:
    | "REFERENCE_VERIFIED"
    | "REFERENCE_MISMATCH"
    | "REFERENCE_NOT_FOUND"
    | "OUTDATED_APPROVAL"
    | "UNAPPROVED_QUOTA"
    | "ADVERSE_STANDING"
    | string;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  message: string;
  reference_source: string;
  effective_date?: string | null;
}

export interface ReferenceMatchReport {
  application_id: string;
  institution_id: string;
  reference_matched: boolean;
  institution_reference_id?: string | null;
  aicte_permanent_id?: string | null;
  legal_name?: string | null;
  verification_status: "OFFICIAL_VERIFIED" | "PROVISIONAL_PENDING" | "SYNTHETIC_BENCHMARK" | "UNVERIFIED" | string;
  source_provenance?: string | null;
  data_freshness_date?: string | null;
  is_official: boolean;
  standing_status?: string | null;
  matched_fields: Record<string, ReferenceMatchFieldResult>;
  findings: ReferenceMatchFinding[];
  programmes_summary: ApprovedProgrammeReference[];
  latest_approval?: InstitutionApprovalHistoryReference | null;
  recommendation: "AUTO_VERIFIED" | "MANUAL_SCRUTINY_REQUIRED" | "REJECT_UNAUTHORIZED" | string;
}


export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface LoginPayload {
  email: string;
  password: string;
}
