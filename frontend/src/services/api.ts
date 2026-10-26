import {
  DashboardSummary,
  TrendPoint,
  ApplicationListItem,
  ApplicationDetail,
  Institution,
  DocumentItem,
  DocumentExtraction,
  ChecklistItem,
  RegulatoryRule,
  ComplianceEvaluationReport,
  PaginatedResponse,
  CreateApplicationPayload,
  CreateInstitutionPayload,
} from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000/api";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...options?.headers,
      },
    });

    if (!res.ok) {
      let errorMessage = `HTTP error ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) {
          errorMessage = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // fallback
      }
      throw new Error(errorMessage);
    }

    return await res.json();
  } catch (err: any) {
    if (err.name === "TypeError" && err.message?.toLowerCase().includes("failed to fetch")) {
      console.error(`Network / Connection Error [${endpoint}]:`, err);
      throw new Error("Unable to connect to AICTE validation server. Please ensure the backend service is running on port 8000.");
    }
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // Health
  checkHealth: () => request<{ status: string; database: string }>("/health"),

  // Dashboard
  getDashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
  getDashboardTrends: (days = 14) => request<{ trends: TrendPoint[] }>(`/dashboard/trends?days=${days}`),

  // Applications
  getApplications: (params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    category?: string;
    academic_year?: string;
  }) => {
    const query = new URLSearchParams();
    if (params.page) query.append("page", params.page.toString());
    if (params.limit) query.append("limit", params.limit.toString());
    if (params.search) query.append("search", params.search);
    if (params.status && params.status !== "All") query.append("status", params.status);
    if (params.category && params.category !== "All") query.append("category", params.category);
    if (params.academic_year && params.academic_year !== "All") query.append("academic_year", params.academic_year);

    return request<PaginatedResponse<ApplicationListItem>>(`/applications?${query.toString()}`);
  },

  getApplicationById: (id: string) => request<ApplicationDetail>(`/applications/${id}`),

  createApplication: (payload: CreateApplicationPayload) =>
    request<ApplicationDetail>("/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateApplication: (id: string, payload: Partial<ApplicationDetail>) =>
    request<ApplicationDetail>(`/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Phase 2 Documents APIs
  getApplicationDocuments: (applicationId: string, page = 1, limit = 20) =>
    request<PaginatedResponse<DocumentItem>>(`/applications/${applicationId}/documents?page=${page}&limit=${limit}`),

  getApplicationChecklist: (applicationId: string) =>
    request<ChecklistItem[]>(`/applications/${applicationId}/checklist`),

  uploadDocument: (applicationId: string, formData: FormData) =>
    request<DocumentItem>(`/applications/${applicationId}/documents`, {
      method: "POST",
      body: formData,
    }),

  getDocumentMetadata: (documentId: string) =>
    request<DocumentItem>(`/documents/${documentId}`),

  getDocumentExtraction: (documentId: string) =>
    request<DocumentExtraction>(`/documents/${documentId}/extraction`),

  triggerDocumentProcess: (documentId: string) =>
    request<DocumentItem>(`/documents/${documentId}/process`, {
      method: "POST",
    }),

  correctDocumentField: (documentId: string, fieldName: string, correctedValue: string, reason?: string) =>
    request<DocumentExtraction>(`/documents/${documentId}/extraction`, {
      method: "PATCH",
      body: JSON.stringify({
        field_name: fieldName,
        corrected_value: correctedValue,
        reason,
      }),
    }),

  getDocumentVersions: (documentId: string) =>
    request<DocumentItem[]>(`/documents/${documentId}/versions`),

  getDocumentFileUrl: (documentId: string) => `${API_BASE}/documents/${documentId}/file`,

  // Phase 3 Compliance Engine APIs
  getComplianceRules: () =>
    request<RegulatoryRule[]>("/compliance/rules"),

  runApplicationCompliance: (applicationId: string) =>
    request<ComplianceEvaluationReport>(`/applications/${applicationId}/compliance/evaluate`, {
      method: "POST",
    }),

  getApplicationComplianceReport: (applicationId: string) =>
    request<{
      application_id: string;
      application_identifier: string;
      compliance_status: string;
      last_evaluated_at?: string;
      rule_version: string;
      findings: any[];
    }>(`/applications/${applicationId}/compliance/report`),

  // Phase 4 Risk Engine APIs
  getRiskConfig: () =>
    request<import("../types").RiskConfig>("/risk/config"),

  runApplicationRiskEvaluation: (applicationId: string) =>
    request<import("../types").RiskAssessmentReport>(`/applications/${applicationId}/risk/evaluate`, {
      method: "POST",
    }),

  getApplicationRiskReport: (applicationId: string) =>
    request<import("../types").RiskAssessmentReport>(`/applications/${applicationId}/risk/report`),

  // Institutions
  getInstitutions: (params?: { page?: number; limit?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.search) query.append("search", params.search);

    return request<PaginatedResponse<Institution>>(`/institutions?${query.toString()}`);
  },

  createInstitution: (payload: CreateInstitutionPayload) =>
    request<Institution>("/institutions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
