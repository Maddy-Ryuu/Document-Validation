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
  DocumentReviewItem,
  QueueItem,
  AuditEventItem,
  AnalyticsReport,
  SystemSettings,
  InstitutionReferenceRecord,
  ReferenceMatchReport,
  AuthUser,
  AuthResponse,
  LoginPayload,
} from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000/api";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("aicte_auth_token") : null;
    const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...authHeaders,
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

  getDocumentFileUrl: (documentId: string) =>
    `${API_BASE}/documents/${documentId}/file?auth_token=aicte-reviewer-session-auth`,

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

  updateInstitution: (id: string, payload: Partial<CreateInstitutionPayload>) =>
    request<Institution>(`/institutions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteInstitution: (id: string) =>
    request<{ success: boolean; message: string; deleted_institution_id: string }>(`/institutions/${id}`, {
      method: "DELETE",
    }),

  // Sidebar Modules APIs
  getAllDocuments: (params?: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    document_type?: string;
    application_id?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.search) query.append("search", params.search);
    if (params?.status && params.status !== "All") query.append("status", params.status);
    if (params?.document_type && params.document_type !== "All") query.append("document_type", params.document_type);
    if (params?.application_id) query.append("application_id", params.application_id);

    return request<PaginatedResponse<DocumentReviewItem>>(`/documents?${query.toString()}`);
  },

  reviewDocument: (documentId: string, action: string, comments?: string) => {
    const query = new URLSearchParams();
    query.append("action", action);
    if (comments) query.append("comments", comments);

    return request<{ id: string; processing_status: string }>(`/documents/${documentId}/review?${query.toString()}`, {
      method: "POST",
    });
  },

  getReviewQueue: (params?: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    priority?: string;
    category?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.search) query.append("search", params.search);
    if (params?.status && params.status !== "All") query.append("status", params.status);
    if (params?.priority && params.priority !== "All") query.append("priority", params.priority);
    if (params?.category && params.category !== "All") query.append("category", params.category);

    return request<PaginatedResponse<QueueItem>>(`/queue?${query.toString()}`);
  },

  getAuditEvents: (params?: {
    page?: number;
    limit?: number;
    entity_type?: string;
    action?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.entity_type && params.entity_type !== "All") query.append("entity_type", params.entity_type);
    if (params?.action && params.action !== "All") query.append("action", params.action);
    if (params?.search) query.append("search", params.search);

    return request<PaginatedResponse<AuditEventItem>>(`/audit-events?${query.toString()}`);
  },

  getAnalyticsReport: () =>
    request<AnalyticsReport>("/reports/analytics"),

  getSystemSettings: () =>
    request<SystemSettings>("/settings/system"),

  rerunVerification: (applicationId: string) =>
    request<{ application_id: string; compliance: any; risk: any }>(`/verification/rerun/${applicationId}`, {
      method: "POST",
    }),

  // Phase 2 Authoritative Reference Data & Cross-Verification APIs
  getApplicationReferenceMatch: (applicationId: string) =>
    request<ReferenceMatchReport>(`/applications/${applicationId}/reference-match`),

  runApplicationReferenceMatch: (applicationId: string) =>
    request<ReferenceMatchReport>(`/applications/${applicationId}/reference-match`, {
      method: "POST",
    }),

  getReferenceInstitutions: (params?: { state?: string; standing_status?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.state) query.append("state", params.state);
    if (params?.standing_status) query.append("standing_status", params.standing_status);
    if (params?.search) query.append("search", params.search);
    return request<InstitutionReferenceRecord[]>(`/reference-data/institutions?${query.toString()}`);
  },

  // Authentication APIs
  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const res = await request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (res.access_token) {
      localStorage.setItem("aicte_auth_token", res.access_token);
      localStorage.setItem("aicte_auth_user", JSON.stringify(res.user));
    }
    return res;
  },

  logout: async (): Promise<void> => {
    try {
      await request<{ message: string }>("/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem("aicte_auth_token");
      localStorage.removeItem("aicte_auth_user");
    }
  },

  getCurrentUser: async (): Promise<AuthUser | null> => {
    const token = localStorage.getItem("aicte_auth_token");
    if (!token) return null;
    try {
      return await request<AuthUser>("/auth/me");
    } catch {
      localStorage.removeItem("aicte_auth_token");
      localStorage.removeItem("aicte_auth_user");
      return null;
    }
  },

  deleteApplication: (id: string) =>
    request<{ success: boolean; message: string; deleted_application_id: string }>(`/applications/${id}`, {
      method: "DELETE",
    }),

  getReferenceInstitutionById: (refId: string) =>
    request<InstitutionReferenceRecord>(`/reference-data/institutions/${refId}`),
};
