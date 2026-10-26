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
  criticality: "Mandatory" | "Required" | "Optional" | string;
  is_mandatory: boolean;
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
