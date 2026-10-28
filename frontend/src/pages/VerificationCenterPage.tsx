import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Search,
  Filter,
  ShieldCheck,
  Building,
  FileText,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Play,
  Layers,
  AlertCircle,
  XCircle,
  Clock,
  Database,
  Calendar,
  Scale,
  FileSearch,
  Eye,
  Check,
  X,
  ArrowLeft,
  Info,
} from "lucide-react";
import { api } from "../services/api";
import {
  ApplicationListItem,
  ReferenceMatchReport,
  InstitutionReferenceRecord,
  DocumentItem,
  DocumentExtraction,
} from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { DocumentViewer } from "../components/DocumentViewer";
import { formatDate, formatDateTime } from "../lib/utils";

interface VerificationCenterPageProps {
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const VerificationCenterPage: React.FC<VerificationCenterPageProps> = ({
  onSelectApplication,
  refreshTrigger,
}) => {
  // Application list state
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Rerun verification state
  const [rerunningId, setRerunningId] = useState<string | null>(null);
  const [rerunFeedback, setRerunFeedback] = useState<string | null>(null);

  // Active Application Inspection Dossier
  const [inspectedAppId, setInspectedAppId] = useState<string | null>(null);
  const [inspectedAppMeta, setInspectedAppMeta] = useState<ApplicationListItem | null>(null);
  const [inspectorTab, setInspectorTab] = useState<"reference_match" | "document_extraction" | "side_by_side">("side_by_side");

  // Reference match state for inspected application
  const [refMatchReport, setRefMatchReport] = useState<ReferenceMatchReport | null>(null);
  const [loadingRefMatch, setLoadingRefMatch] = useState(false);
  const [refMatchError, setRefMatchError] = useState<string | null>(null);
  const [evaluatingRefMatch, setEvaluatingRefMatch] = useState(false);

  // Document extraction state for inspected application
  const [appDocs, setAppDocs] = useState<DocumentItem[]>([]);
  const [docExtractions, setDocExtractions] = useState<Record<string, DocumentExtraction>>({});
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [docsError, setDocsError] = useState<string | null>(null);
  const [selectedDocForViewer, setSelectedDocForViewer] = useState<DocumentItem | null>(null);

  // Authoritative Central Registry Browser Modal
  const [isRegistryModalOpen, setIsRegistryModalOpen] = useState(false);
  const [registryRecords, setRegistryRecords] = useState<InstitutionReferenceRecord[]>([]);
  const [loadingRegistry, setLoadingRegistry] = useState(false);
  const [registrySearch, setRegistrySearch] = useState("");
  const [registryStandingFilter, setRegistryStandingFilter] = useState("All");

  useEffect(() => {
    fetchApplications();
  }, [page, statusFilter, refreshTrigger]);

  useEffect(() => {
    if (inspectedAppId) {
      loadInspectionData(inspectedAppId);
    }
  }, [inspectedAppId]);

  const fetchApplications = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getApplications({
        page,
        limit: 10,
        search: search.trim() || undefined,
        status: statusFilter !== "All" ? statusFilter : undefined,
      });
      setApplications(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      setError(err.message || "Failed to load verification status");
    } finally {
      setLoading(false);
    }
  };

  const loadInspectionData = async (appId: string) => {
    setLoadingRefMatch(true);
    setLoadingDocs(true);
    setRefMatchError(null);
    setDocsError(null);

    // 1. Fetch Reference-Match Report
    try {
      const match = await api.getApplicationReferenceMatch(appId);
      setRefMatchReport(match);
    } catch (err: any) {
      setRefMatchError(err.message || "Failed to load reference match report");
    } finally {
      setLoadingRefMatch(false);
    }

    // 2. Fetch Application Documents & Extractions
    try {
      const docsRes = await api.getApplicationDocuments(appId, 1, 50);
      setAppDocs(docsRes.items);

      // Load extractions for each document
      const extractionsMap: Record<string, DocumentExtraction> = {};
      await Promise.all(
        docsRes.items.map(async (doc) => {
          try {
            const ext = await api.getDocumentExtraction(doc.id);
            if (ext) extractionsMap[doc.id] = ext;
          } catch {
            // Ignored if extraction not ready yet
          }
        })
      );
      setDocExtractions(extractionsMap);
    } catch (err: any) {
      setDocsError(err.message || "Failed to load statutory documents");
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleRunReferenceMatch = async () => {
    if (!inspectedAppId) return;
    setEvaluatingRefMatch(true);
    setRefMatchError(null);
    try {
      const updatedReport = await api.runApplicationReferenceMatch(inspectedAppId);
      setRefMatchReport(updatedReport);
      setRerunFeedback(`Reference cross-verification evaluated: ${updatedReport.recommendation}`);
      setTimeout(() => setRerunFeedback(null), 4000);
    } catch (err: any) {
      setRefMatchError(err.message || "Cross-verification evaluation failed");
    } finally {
      setEvaluatingRefMatch(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchApplications();
  };

  const handleRerunVerification = async (appId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRerunningId(appId);
    setRerunFeedback(null);
    try {
      const res = await api.rerunVerification(appId);
      setRerunFeedback(`Verification complete for ${appId}. Compliance: ${res.compliance?.compliance_status || "Evaluated"}`);
      setTimeout(() => setRerunFeedback(null), 4000);
      fetchApplications();
    } catch (err: any) {
      alert(`Verification run failed: ${err.message}`);
    } finally {
      setRerunningId(null);
    }
  };

  const openRegistryBrowser = async () => {
    setIsRegistryModalOpen(true);
    setLoadingRegistry(true);
    try {
      const records = await api.getReferenceInstitutions({
        search: registrySearch.trim() || undefined,
        standing_status: registryStandingFilter !== "All" ? registryStandingFilter : undefined,
      });
      setRegistryRecords(records);
    } catch (err: any) {
      alert(`Failed to load registry: ${err.message}`);
    } finally {
      setLoadingRegistry(false);
    }
  };

  const handleRegistrySearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingRegistry(true);
    try {
      const records = await api.getReferenceInstitutions({
        search: registrySearch.trim() || undefined,
        standing_status: registryStandingFilter !== "All" ? registryStandingFilter : undefined,
      });
      setRegistryRecords(records);
    } catch (err: any) {
      alert(`Failed to filter registry: ${err.message}`);
    } finally {
      setLoadingRegistry(false);
    }
  };

  // Helper for recommendation styling
  const renderRecommendationBanner = (recommendation: string, isOfficial: boolean, status: string) => {
    const isVerified = recommendation === "AUTO_VERIFIED" && isOfficial;
    const isReject = recommendation === "REJECT_UNAUTHORIZED";

    return (
      <div
        className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
          isVerified
            ? "bg-emerald-50/70 border-emerald-300 text-emerald-900"
            : isReject
            ? "bg-red-50/80 border-red-300 text-red-900"
            : "bg-amber-50/80 border-amber-300 text-amber-900"
        }`}
      >
        <div className="flex items-start space-x-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
              isVerified
                ? "bg-emerald-200/60 text-emerald-700"
                : isReject
                ? "bg-red-200/60 text-red-700"
                : "bg-amber-200/60 text-amber-800"
            }`}
          >
            {isVerified ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : isReject ? (
              <XCircle className="w-5 h-5" />
            ) : (
              <AlertTriangle className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold uppercase tracking-wider">
                Regulatory Decision: {recommendation.replace(/_/g, " ")}
              </span>
              <StatusBadge status={status} />
            </div>
            <p className="text-xs mt-1">
              {isVerified
                ? "All submitted credentials match authoritative AICTE Central Portal registry records in good standing."
                : isReject
                ? "Severe discrepancies detected: unauthorized quota submission, adverse disciplinary standing, or identity mismatch."
                : status === "SYNTHETIC_BENCHMARK"
                ? "Synthetic demonstration benchmark match: cannot establish official statutory verification without authentic registry records. Routing to Manual Scrutiny Queue."
                : "Manual scrutiny required: Submitted records are unverified, missing from central registry, or require officer examination."}
            </p>
          </div>
        </div>

        <button
          onClick={handleRunReferenceMatch}
          disabled={evaluatingRefMatch}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface shadow-xs shrink-0 disabled:opacity-50"
        >
          <RotateCw className={`w-3.5 h-3.5 text-primary-orange ${evaluatingRefMatch ? "animate-spin" : ""}`} />
          <span>{evaluatingRefMatch ? "Matching..." : "Re-evaluate Match"}</span>
        </button>
      </div>
    );
  };

  // Helper for finding badge styling
  const renderFindingBadge = (type: string) => {
    switch (type) {
      case "REFERENCE_VERIFIED":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-800 rounded border border-emerald-300">Verified</span>;
      case "REFERENCE_MISMATCH":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-100 text-red-800 rounded border border-red-300">Identity Mismatch</span>;
      case "REFERENCE_NOT_FOUND":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-100 text-amber-800 rounded border border-amber-300">Record Not Found</span>;
      case "OUTDATED_APPROVAL":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-orange-100 text-orange-800 rounded border border-orange-300">Outdated Approval</span>;
      case "UNAPPROVED_QUOTA":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-rose-100 text-rose-800 rounded border border-rose-300">Unapproved Quota</span>;
      case "ADVERSE_STANDING":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-100 text-red-900 rounded border border-red-400">Adverse Standing</span>;
      case "SYNTHETIC_REFERENCE_BENCHMARK":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-100 text-amber-900 rounded border border-amber-300">Synthetic Benchmark</span>;
      case "PROGRAMME_INTAKE_MISMATCH":
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-100 text-red-800 rounded border border-red-300">Programme / Intake Mismatch</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-gray-100 text-gray-800 rounded border border-gray-300">{type}</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-primary-text tracking-tight">Verification Center</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
              Active Module
            </span>
          </div>
          <p className="text-xs text-secondary-text mt-0.5">
            Consolidated regulatory rule verification, statutory evidence extraction, and official AICTE registry cross-verification
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={openRegistryBrowser}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
            title="Browse Authoritative AICTE Central Registry"
          >
            <Database className="w-3.5 h-3.5 text-primary-orange" />
            <span>AICTE Central Registry</span>
          </button>

          <button
            onClick={fetchApplications}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
          >
            <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {rerunFeedback && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{rerunFeedback}</span>
          </div>
          <button onClick={() => setRerunFeedback(null)}>
            <XCircle className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Verification Framework Info Banner */}
      <div className="bg-gradient-to-r from-orange-50/70 via-white to-orange-50/40 p-4 rounded-lg border border-orange-200/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <div className="w-9 h-9 rounded-lg bg-primary-orange/10 flex items-center justify-center text-primary-orange shrink-0 mt-0.5">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-primary-text uppercase tracking-wider">
              Approval Process Handbook (APH 2026-27) Dual Verification Pipeline
            </h3>
            <p className="text-xs text-secondary-text mt-0.5 max-w-2xl">
              1. <strong>Statutory Document Extraction:</strong> Deterministic vector text & OCR parsing across 7 EoA checklist categories.<br />
              2. <strong>Central Registry Cross-Verification:</strong> Cross-checks applicant identifiers, sanctioned intake, and approval history against authoritative reference records.
            </p>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md w-full">
          <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by application identifier, institution, city, or state..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Verification Statuses</option>
            <option value="Action Required">Action Required</option>
            <option value="Under Validation">Under Validation</option>
            <option value="Verified">Verified</option>
            <option value="Approved">Approved</option>
            <option value="Rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
            <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
            <span>Evaluating application verification states...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <span>{error}</span>
          </div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center text-secondary-text text-xs">
            <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-border" />
            <p className="font-medium text-primary-text">No verification records found</p>
            <p className="mt-1">Try adjusting your search criteria or filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-muted/50 text-[11px] font-semibold text-secondary-text uppercase tracking-wider">
                  <th className="py-3 px-4">Application</th>
                  <th className="py-3 px-4">Institution Context</th>
                  <th className="py-3 px-4">Category & Year</th>
                  <th className="py-3 px-4">Status & Evidence</th>
                  <th className="py-3 px-4">Compliance Findings</th>
                  <th className="py-3 px-4 text-right">Verification Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {applications.map((app) => {
                  const isRerunning = rerunningId === app.id;
                  const isInspecting = inspectedAppId === app.id;
                  return (
                    <tr
                      key={app.id}
                      onClick={() => {
                        setInspectedAppId(app.id);
                        setInspectedAppMeta(app);
                      }}
                      className={`hover:bg-surface/50 cursor-pointer transition-colors ${
                        isInspecting ? "bg-orange-50/40 border-l-4 border-l-primary-orange" : ""
                      }`}
                    >
                      <td className="py-3 px-4 font-semibold text-primary-orange">
                        {app.application_identifier}
                        <div className="text-[10px] text-secondary-text font-normal mt-0.5">
                          Submitted {formatDate(app.submission_date)}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-medium text-primary-text truncate max-w-xs">
                          {app.institution_name}
                        </div>
                        <div className="text-[11px] text-secondary-text">
                          {app.institution_city}, {app.institution_state}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="font-medium text-primary-text">{app.application_category}</span>
                        <div className="text-[11px] text-secondary-text">{app.academic_year}</div>
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge status={app.status} />
                        <div className="text-[10px] text-secondary-text mt-1 flex items-center space-x-1">
                          <FileText className="w-3 h-3 text-secondary-text" />
                          <span>{app.documents_count} document(s) uploaded</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        {app.findings_count > 0 ? (
                          <div className="flex items-center space-x-1 text-red-600 font-medium">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>{app.findings_count} Finding(s) Open</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-1 text-emerald-600 font-medium">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>0 Findings Reported</span>
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => {
                              setInspectedAppId(app.id);
                              setInspectedAppMeta(app);
                            }}
                            className="flex items-center space-x-1 px-2.5 py-1 bg-primary-orange/10 text-primary-orange border border-primary-orange/20 hover:bg-primary-orange/20 rounded text-xs font-semibold transition-colors"
                            title="Cross-Verify and Inspect Evidence"
                          >
                            <Scale className="w-3 h-3" />
                            <span>Cross-Verify</span>
                          </button>

                          <button
                            disabled={isRerunning}
                            onClick={(e) => handleRerunVerification(app.id, e)}
                            className="flex items-center space-x-1 px-2.5 py-1 bg-white border border-border text-primary-text hover:bg-surface rounded text-xs font-medium shadow-xs transition-colors"
                            title="Rerun Regulatory Rule Engine"
                          >
                            <Play className={`w-3 h-3 text-primary-orange ${isRerunning ? "animate-spin" : ""}`} />
                            <span>{isRerunning ? "Running..." : "Evaluate"}</span>
                          </button>

                          <button
                            onClick={() => onSelectApplication(app.id)}
                            className="p-1 text-secondary-text hover:text-primary-orange transition-colors"
                            title="Open Dossier"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && applications.length > 0 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-xs text-secondary-text">
            <span>
              Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, total)} of {total} applications
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1 rounded border border-border hover:bg-surface disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span>Page {page} of {pages}</span>
              <button
                disabled={page >= pages}
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                className="p-1 rounded border border-border hover:bg-surface disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* INTEGRATED DUAL SCRUTINY DOSSIER PANEL (Phase 2 Cross-Verification + Docs) */}
      {/* ========================================================================= */}
      {inspectedAppId && inspectedAppMeta && (
        <div id="cross-verification-dossier" className="bg-white rounded-lg border-2 border-primary-orange/40 shadow-md p-6 space-y-6 animate-in fade-in duration-200">
          {/* Inspection Panel Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
            <div>
              <div className="flex items-center space-x-3">
                <span className="px-2.5 py-1 text-xs font-bold bg-primary-orange text-white rounded">
                  Active Cross-Verification Dossier
                </span>
                <h3 className="text-lg font-bold text-primary-text">
                  {inspectedAppMeta.application_identifier}
                </h3>
                <span className="text-xs text-secondary-text">({inspectedAppMeta.application_category})</span>
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-secondary-text mt-1.5">
                <span className="font-semibold text-primary-text">{inspectedAppMeta.institution_name}</span>
                <span>•</span>
                <span>{inspectedAppMeta.institution_city}, {inspectedAppMeta.institution_state}</span>
                <span>•</span>
                <span>Academic Year: {inspectedAppMeta.academic_year}</span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Tab Selector */}
              <div className="flex items-center p-0.5 bg-surface-muted border border-border rounded-lg text-xs">
                <button
                  onClick={() => setInspectorTab("side_by_side")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    inspectorTab === "side_by_side" ? "bg-white text-primary-orange shadow-xs" : "text-secondary-text"
                  }`}
                >
                  Side-by-Side
                </button>
                <button
                  onClick={() => setInspectorTab("reference_match")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    inspectorTab === "reference_match" ? "bg-white text-primary-orange shadow-xs" : "text-secondary-text"
                  }`}
                >
                  Central Registry
                </button>
                <button
                  onClick={() => setInspectorTab("document_extraction")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    inspectorTab === "document_extraction" ? "bg-white text-primary-orange shadow-xs" : "text-secondary-text"
                  }`}
                >
                  Document OCR
                </button>
              </div>

              <button
                onClick={() => onSelectApplication(inspectedAppId)}
                className="flex items-center space-x-1 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded hover:bg-surface"
                title="Open Complete Dossier Page"
              >
                <span>Full Page</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setInspectedAppId(null)}
                className="p-1.5 text-secondary-text hover:text-primary-text rounded border border-border"
                title="Close Inspector"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* SECTION 1: RECOMMENDATION BANNER */}
          {refMatchReport ? (
            renderRecommendationBanner(
              refMatchReport.recommendation,
              refMatchReport.is_official,
              refMatchReport.verification_status
            )
          ) : loadingRefMatch ? (
            <div className="p-4 bg-surface-muted rounded border border-border text-xs text-secondary-text flex items-center space-x-2">
              <RotateCw className="w-4 h-4 animate-spin text-primary-orange" />
              <span>Querying AICTE Central Registry for cross-verification...</span>
            </div>
          ) : refMatchError ? (
            <div className="p-4 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center justify-between">
              <span>{refMatchError}</span>
              <button
                onClick={() => loadInspectionData(inspectedAppId)}
                className="underline font-semibold ml-2"
              >
                Retry
              </button>
            </div>
          ) : null}

          {/* DUAL CONTENT GRID */}
          <div
            className={`grid gap-6 ${
              inspectorTab === "side_by_side"
                ? "grid-cols-1 lg:grid-cols-2"
                : "grid-cols-1"
            }`}
          >
            {/* ================================================================= */}
            {/* VIEW A: CENTRAL REGISTRY REFERENCE-DATA CROSS-VERIFICATION       */}
            {/* ================================================================= */}
            {(inspectorTab === "side_by_side" || inspectorTab === "reference_match") && (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-border">
                  <div className="flex items-center space-x-2">
                    <Database className="w-4 h-4 text-primary-orange" />
                    <h4 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                      Authoritative Central Registry Matching
                    </h4>
                  </div>
                  {refMatchReport && (
                    <span className="text-[10px] text-secondary-text">
                      {refMatchReport.data_freshness_date ? `Data Freshness: ${formatDate(refMatchReport.data_freshness_date)}` : "Live Registry Sync"}
                    </span>
                  )}
                </div>

                {loadingRefMatch ? (
                  <div className="p-8 text-center text-xs text-secondary-text flex flex-col items-center justify-center space-y-2">
                    <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
                    <span>Matching application against AICTE permanent records...</span>
                  </div>
                ) : refMatchReport ? (
                  <div className="space-y-4 text-xs">
                    {/* Provenance & Standing Header Card */}
                    <div className="bg-surface-muted/40 p-3.5 rounded-lg border border-border space-y-2.5">
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-secondary-text block">AICTE Permanent ID:</span>
                          <span className="font-semibold text-primary-text">
                            {refMatchReport.aicte_permanent_id || "Unresolved in Registry"}
                          </span>
                        </div>
                        <div>
                          <span className="text-secondary-text block">Registered Legal Name:</span>
                          <span className="font-semibold text-primary-text">
                            {refMatchReport.legal_name || "Record Not Linked"}
                          </span>
                        </div>
                        <div>
                          <span className="text-secondary-text block">Source Provenance:</span>
                          <span className="font-medium text-primary-text">
                            {refMatchReport.source_provenance || "AICTE Central Registry"}
                          </span>
                        </div>
                        <div>
                          <span className="text-secondary-text block">Standing Status:</span>
                          <span className={`font-semibold ${
                            refMatchReport.standing_status === "APPROVED_IN_GOOD_STANDING" || refMatchReport.standing_status === "Approved"
                              ? "text-emerald-700"
                              : "text-red-700"
                          }`}>
                            {refMatchReport.standing_status || "UNVERIFIED"}
                          </span>
                        </div>
                      </div>

                      {/* Official vs Synthetic Benchmark Marker */}
                      <div className="pt-2 border-t border-border/60 flex items-center justify-between text-[10px]">
                        <span className="text-secondary-text">Registry Authenticity:</span>
                        {refMatchReport.is_official ? (
                          <span className="text-emerald-700 font-semibold flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Official Statutory AICTE Record</span>
                          </span>
                        ) : (
                          <span className="text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Demonstration Benchmark / Unverified
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Matched Fields & Discrepancies Table */}
                    <div>
                      <h5 className="font-semibold text-primary-text text-[11px] mb-1.5 flex items-center space-x-1">
                        <Scale className="w-3.5 h-3.5 text-primary-orange" />
                        <span>Field-by-Field Verification & Discrepancy Scrutiny</span>
                      </h5>
                      <div className="border border-border rounded-md overflow-hidden">
                        <table className="w-full text-left border-collapse">
                          <thead>
                            <tr className="bg-surface-muted/60 text-[10px] font-semibold text-secondary-text uppercase border-b border-border">
                              <th className="py-2 px-3">Field</th>
                              <th className="py-2 px-3">Submitted Value</th>
                              <th className="py-2 px-3">Official Record</th>
                              <th className="py-2 px-3 text-right">Result</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border text-[11px]">
                            {Object.entries(refMatchReport.matched_fields || {}).map(([key, field]) => (
                              <tr key={key} className={!field.match ? "bg-red-50/40" : ""}>
                                <td className="py-2 px-3 font-medium text-primary-text capitalize">
                                  {key.replace(/_/g, " ")}
                                </td>
                                <td className="py-2 px-3 text-secondary-text truncate max-w-[140px]">
                                  {field.submitted_value || "—"}
                                </td>
                                <td className="py-2 px-3 text-primary-text font-medium truncate max-w-[140px]">
                                  {field.official_value || "—"}
                                </td>
                                <td className="py-2 px-3 text-right">
                                  {field.match ? (
                                    <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold">
                                      <Check className="w-3 h-3" />
                                      <span>Match</span>
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center space-x-1 text-red-600 font-semibold" title={field.notes || "Mismatch"}>
                                      <X className="w-3 h-3" />
                                      <span>Mismatch</span>
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Explainable Findings */}
                    {refMatchReport.findings && refMatchReport.findings.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-primary-text text-[11px] mb-1.5 flex items-center space-x-1">
                          <AlertTriangle className="w-3.5 h-3.5 text-primary-orange" />
                          <span>Explainable Cross-Verification Findings</span>
                        </h5>
                        <div className="space-y-1.5">
                          {refMatchReport.findings.map((f, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 rounded border border-border bg-surface-muted/30 flex items-start justify-between gap-2"
                            >
                              <div className="space-y-0.5">
                                <div className="flex items-center space-x-2">
                                  {renderFindingBadge(f.finding_type)}
                                  <span className="text-[10px] text-secondary-text font-medium">
                                    Severity: {f.severity}
                                  </span>
                                </div>
                                <p className="text-[11px] text-primary-text mt-1">{f.message}</p>
                                <span className="text-[10px] text-secondary-text block">
                                  Source: {f.reference_source} {f.effective_date ? `(Eff: ${f.effective_date})` : ""}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Approved Programmes & Sanctioned Intake (when available) */}
                    {refMatchReport.programmes_summary && refMatchReport.programmes_summary.length > 0 && (
                      <div>
                        <h5 className="font-semibold text-primary-text text-[11px] mb-1.5 flex items-center space-x-1">
                          <Building className="w-3.5 h-3.5 text-primary-orange" />
                          <span>Officially Approved Programmes & Sanctioned Intake</span>
                        </h5>
                        <div className="border border-border rounded-md overflow-hidden">
                          <table className="w-full text-left border-collapse text-[10px]">
                            <thead>
                              <tr className="bg-surface-muted/60 font-semibold text-secondary-text border-b border-border">
                                <th className="py-1.5 px-2.5">Course / Programme</th>
                                <th className="py-1.5 px-2">Level</th>
                                <th className="py-1.5 px-2">Intake</th>
                                <th className="py-1.5 px-2">NRI Quota</th>
                                <th className="py-1.5 px-2">Accreditation</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                              {refMatchReport.programmes_summary.map((prog) => (
                                <tr key={prog.id} className="hover:bg-surface/50">
                                  <td className="py-1.5 px-2.5 font-medium text-primary-text">{prog.course_name}</td>
                                  <td className="py-1.5 px-2 text-secondary-text">{prog.level}</td>
                                  <td className="py-1.5 px-2 font-bold text-primary-text">{prog.approved_intake}</td>
                                  <td className="py-1.5 px-2">
                                    {prog.nri_quota_approved ? (
                                      <span className="text-emerald-700 font-medium">Approved ({prog.nri_quota_intake})</span>
                                    ) : (
                                      <span className="text-secondary-text">None</span>
                                    )}
                                  </td>
                                  <td className="py-1.5 px-2 text-secondary-text">{prog.accreditation_status}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Approval History Continuity (when available) */}
                    {refMatchReport.latest_approval && (
                      <div className="p-3 bg-surface-muted/30 rounded border border-border text-[11px] space-y-1">
                        <span className="text-secondary-text block font-semibold text-[10px] uppercase">
                          Latest Approval History Record:
                        </span>
                        <div className="flex items-center justify-between">
                          <span>
                            <strong>Academic Year:</strong> {refMatchReport.latest_approval.academic_year}
                          </span>
                          <span>
                            <strong>EoA No:</strong> {refMatchReport.latest_approval.eoa_application_number || "Continuous"}
                          </span>
                          <span>
                            <strong>Sanctioned Seats:</strong> {refMatchReport.latest_approval.total_sanctioned_intake}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-secondary-text border border-dashed border-border rounded-lg">
                    <p className="font-semibold text-primary-text">No cross-verification report generated yet.</p>
                    <p className="mt-1">Evaluate the application against the AICTE master registry.</p>
                    <button
                      onClick={handleRunReferenceMatch}
                      disabled={evaluatingRefMatch}
                      className="mt-3 px-3 py-1.5 bg-primary-orange text-white text-xs font-semibold rounded shadow-xs hover:bg-primary-orange/90"
                    >
                      {evaluatingRefMatch ? "Cross-Verifying..." : "Run Cross-Verification Now"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ================================================================= */}
            {/* VIEW B: STATUTORY DOCUMENT EXTRACTION & OCR SCRUTINY             */}
            {/* ================================================================= */}
            {(inspectorTab === "side_by_side" || inspectorTab === "document_extraction") && (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-border">
                  <div className="flex items-center space-x-2">
                    <FileSearch className="w-4 h-4 text-primary-orange" />
                    <h4 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                      Statutory Document OCR & Field Extractions
                    </h4>
                  </div>
                  <span className="text-[10px] text-secondary-text">
                    {appDocs.length} uploaded document(s)
                  </span>
                </div>

                {loadingDocs ? (
                  <div className="p-8 text-center text-xs text-secondary-text flex flex-col items-center justify-center space-y-2">
                    <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
                    <span>Loading statutory documents & OCR extractions...</span>
                  </div>
                ) : docsError ? (
                  <div className="p-4 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                    {docsError}
                  </div>
                ) : appDocs.length === 0 ? (
                  <div className="p-6 text-center text-xs text-secondary-text border border-dashed border-border rounded-lg">
                    <FileText className="w-6 h-6 mx-auto mb-1 text-border" />
                    <p className="font-semibold text-primary-text">No documents uploaded for this application</p>
                    <p className="mt-1">Applicant must submit required statutory PDF/image documents.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {appDocs.map((doc) => {
                      const ext = docExtractions[doc.id];
                      return (
                        <div
                          key={doc.id}
                          className="p-3 bg-surface-muted/30 rounded-lg border border-border space-y-2 hover:border-primary-orange/40 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="font-semibold text-primary-text text-xs">
                                  {doc.document_type}
                                </span>
                                <StatusBadge status={doc.processing_status} />
                              </div>
                              <span className="text-[10px] text-secondary-text block mt-0.5">
                                {doc.original_filename} (v{doc.version}) • {formatDateTime(doc.created_at)}
                              </span>
                            </div>

                            <button
                              onClick={() => setSelectedDocForViewer(doc)}
                              className="flex items-center space-x-1 px-2 py-1 bg-white border border-border text-primary-text text-[11px] font-medium rounded hover:bg-surface shrink-0"
                            >
                              <Eye className="w-3 h-3 text-secondary-text" />
                              <span>View</span>
                            </button>
                          </div>

                          {/* Extraction details */}
                          {ext ? (
                            <div className="space-y-1.5 pt-2 border-t border-border/60 text-[10px]">
                              <div className="flex items-center justify-between text-secondary-text">
                                <span>
                                  <strong>Engine:</strong> {ext.extraction_engine || "PyMuPDF"}
                                </span>
                                <span>
                                  <strong>Confidence:</strong>{" "}
                                  {ext.confidence_score ? `${Math.round(ext.confidence_score * 100)}%` : "N/A"}
                                </span>
                                <span>
                                  <strong>Pages:</strong> {ext.page_count}
                                </span>
                              </div>

                              {/* Structured Fields Summary */}
                              {ext.structured_fields && Object.keys(ext.structured_fields).length > 0 && (
                                <div className="p-2 bg-white rounded border border-border/80 space-y-1">
                                  <span className="text-secondary-text font-semibold block text-[10px] uppercase">
                                    Extracted Statutory Fields:
                                  </span>
                                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
                                    {Object.entries(ext.structured_fields).map(([fieldKey, fVal]) => (
                                      <div key={fieldKey} className="truncate">
                                        <span className="text-secondary-text capitalize">
                                          {fieldKey.replace(/_/g, " ")}:
                                        </span>{" "}
                                        <span className="font-medium text-primary-text">
                                          {typeof fVal === "object" ? fVal?.value || JSON.stringify(fVal) : String(fVal)}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Warnings */}
                              {ext.warnings && ext.warnings.length > 0 && (
                                <div className="text-amber-800 bg-amber-50/80 p-1.5 rounded border border-amber-200 text-[10px]">
                                  {ext.warnings.join("; ")}
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-[10px] text-secondary-text italic pt-1">
                              Processing pending or text not yet extracted.
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* AUTHORITATIVE AICTE CENTRAL REGISTRY DIRECTORY MODAL                      */}
      {/* ========================================================================= */}
      {isRegistryModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border border-border shadow-xl max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-primary-orange" />
                <div>
                  <h3 className="text-sm font-bold text-primary-text">
                    Authoritative AICTE Central Registry Catalogue
                  </h3>
                  <p className="text-[11px] text-secondary-text">
                    Official benchmark database of recognized technical institutions and approved programmes
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsRegistryModalOpen(false)}
                className="p-1 text-secondary-text hover:text-primary-text rounded border border-border"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Registry Search Controls */}
            <form onSubmit={handleRegistrySearchSubmit} className="p-4 bg-surface-muted/30 border-b border-border flex flex-col sm:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search legal name, AICTE Permanent ID, city, or state..."
                  value={registrySearch}
                  onChange={(e) => setRegistrySearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
                />
              </div>

              <select
                value={registryStandingFilter}
                onChange={(e) => setRegistryStandingFilter(e.target.value)}
                className="px-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text w-full sm:w-auto"
              >
                <option value="All">All Standing Statuses</option>
                <option value="APPROVED_IN_GOOD_STANDING">Good Standing</option>
                <option value="DEFICIENT">Deficient</option>
                <option value="WITHDRAWN_OR_REVOKED">Withdrawn / Revoked</option>
              </select>

              <button
                type="submit"
                className="px-4 py-1.5 bg-primary-orange text-white text-xs font-semibold rounded shadow-xs hover:bg-primary-orange/90 w-full sm:w-auto"
              >
                Filter Registry
              </button>
            </form>

            {/* Registry List */}
            <div className="overflow-y-auto p-4 flex-1 space-y-3">
              {loadingRegistry ? (
                <div className="p-12 text-center text-xs text-secondary-text flex flex-col items-center justify-center space-y-2">
                  <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
                  <span>Loading official registry records...</span>
                </div>
              ) : registryRecords.length === 0 ? (
                <div className="p-8 text-center text-xs text-secondary-text">
                  No registry records found matching criteria.
                </div>
              ) : (
                <div className="space-y-3 text-xs">
                  {registryRecords.map((reg) => (
                    <div
                      key={reg.id}
                      className="p-3.5 rounded-lg border border-border bg-white space-y-2 hover:border-primary-orange/50 transition-colors"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-primary-text text-sm">
                              {reg.legal_name}
                            </span>
                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                              reg.standing_status === "APPROVED_IN_GOOD_STANDING" || reg.standing_status === "Approved"
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-red-100 text-red-800"
                            }`}>
                              {reg.standing_status.replace(/_/g, " ")}
                            </span>
                          </div>
                          <span className="text-[11px] text-secondary-text block mt-0.5">
                            Permanent ID: <strong className="text-primary-text">{reg.aicte_permanent_id}</strong> • {reg.district_or_city}, {reg.state} ({reg.institution_type})
                          </span>
                        </div>

                        <div className="text-[10px] text-secondary-text text-right sm:shrink-0">
                          <span className="block font-medium text-primary-text">{reg.source_provenance}</span>
                          <span>Verified: {reg.verification_status}</span>
                        </div>
                      </div>

                      {/* Approved Programmes Preview */}
                      {reg.approved_programmes && reg.approved_programmes.length > 0 && (
                        <div className="pt-2 border-t border-border/60 text-[10px]">
                          <span className="text-secondary-text font-semibold block mb-1">
                            Approved Programmes ({reg.approved_programmes.length}):
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {reg.approved_programmes.map((p) => (
                              <span
                                key={p.id}
                                className="px-2 py-0.5 bg-surface-muted rounded border border-border/80 text-primary-text"
                              >
                                {p.course_name} ({p.level}) — <strong>{p.approved_intake} seats</strong>
                                {p.nri_quota_approved ? " [NRI Quota]" : ""}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-3 bg-surface-muted/60 border-t border-border flex justify-end">
              <button
                onClick={() => setIsRegistryModalOpen(false)}
                className="px-4 py-1.5 bg-white border border-border text-primary-text text-xs font-semibold rounded hover:bg-surface"
              >
                Close Registry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Viewer Modal for inspecting PDFs */}
      {selectedDocForViewer && (
        <DocumentViewer
          document={selectedDocForViewer}
          onClose={() => setSelectedDocForViewer(null)}
          onRefresh={() => {
            if (inspectedAppId) loadInspectionData(inspectedAppId);
          }}
          onReplace={() => {
            // Read-only inspection in Verification Center
          }}
        />
      )}
    </div>
  );
};
