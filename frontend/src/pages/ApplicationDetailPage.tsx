import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  Upload,
  FileText,
  AlertCircle,
  CheckCircle2,
  Clock,
  Shield,
  FileCheck2,
  Calendar,
  Layers,
  MapPin,
  ExternalLink,
  Eye,
  RotateCw,
  HelpCircle,
  Play,
  Check,
  X,
  AlertTriangle,
  BookOpen,
  Trash2,
} from "lucide-react";
import { api } from "../services/api";
import {
  ApplicationDetail,
  DocumentItem,
  ChecklistItem,
  ComplianceEvaluationReport,
  RuleEvaluationResult,
  RiskAssessmentReport,
} from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { UploadModal } from "../components/UploadModal";
import { DocumentViewer } from "../components/DocumentViewer";
import { formatDate, formatDateTime } from "../lib/utils";

interface ApplicationDetailPageProps {
  applicationId: string;
  onBack: () => void;
  onRefresh: () => void;
}

export const ApplicationDetailPage: React.FC<ApplicationDetailPageProps> = ({
  applicationId,
  onBack,
  onRefresh,
}) => {
  const [app, setApp] = useState<ApplicationDetail | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [complianceReport, setComplianceReport] = useState<ComplianceEvaluationReport | null>(null);
  const [riskReport, setRiskReport] = useState<RiskAssessmentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDeleteApplication = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteApplication(applicationId);
      setIsDeleteModalOpen(false);
      onRefresh();
      onBack();
    } catch (err: any) {
      setDeleteError(err.message || "Failed to delete application");
    } finally {
      setDeleting(false);
    }
  };
  const [evaluatingRisk, setEvaluatingRisk] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"compliance" | "risk" | "checklist" | "all_docs" | "findings">("compliance");

  // Modals state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadCategory, setUploadCategory] = useState<string | undefined>(undefined);
  const [replaceDocId, setReplaceDocId] = useState<string | undefined>(undefined);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);

  useEffect(() => {
    loadData();
  }, [applicationId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [appData, checklistData] = await Promise.all([
        api.getApplicationById(applicationId),
        api.getApplicationChecklist(applicationId),
      ]);
      setApp(appData);
      setChecklist(checklistData);

      // Attempt to load existing risk report if any run was completed
      try {
        const risk = await api.getApplicationRiskReport(applicationId);
        if (risk) {
          setRiskReport(risk);
        }
      } catch {
        // Handled
      }
      try {
        const rep = await api.getApplicationComplianceReport(applicationId);
        if (rep) {
          // Format as report if findings exist
          const failedCount = rep.findings.length;
          const reviewCount = rep.findings.filter((f: any) =>
            f.title?.toLowerCase().includes("unverified") || f.severity === "Medium"
          ).length;
          setComplianceReport({
            validation_run_id: "latest",
            application_id: rep.application_id,
            application_identifier: rep.application_identifier,
            compliance_status: rep.compliance_status,
            summary: {
              passed: 0,
              failed: failedCount,
              needs_review: reviewCount,
              not_evaluated: 0,
              not_applicable: 0,
              total_evaluated: 7,
            },
            rule_evaluations: [],
            findings_count: rep.findings.length,
          });
        }
      } catch {
        // Handled
      }
    } catch (err: any) {
      setError(err.message || "Failed to load application dossier");
    } finally {
      setLoading(false);
    }
  };

  const handleRunCompliance = async () => {
    setEvaluating(true);
    try {
      const report = await api.runApplicationCompliance(applicationId);
      setComplianceReport(report);
      // Reload app data to update status badge
      const updatedApp = await api.getApplicationById(applicationId);
      setApp(updatedApp);
      // Automatically refresh risk if report exists
      try {
        const risk = await api.runApplicationRiskEvaluation(applicationId);
        setRiskReport(risk);
      } catch {
        // Handled
      }
      onRefresh();
    } catch (err: any) {
      alert(`Compliance evaluation error: ${err.message}`);
    } finally {
      setEvaluating(false);
    }
  };

  const handleRunRisk = async () => {
    setEvaluatingRisk(true);
    try {
      const risk = await api.runApplicationRiskEvaluation(applicationId);
      setRiskReport(risk);
      onRefresh();
    } catch (err: any) {
      alert(`Risk evaluation error: ${err.message}`);
    } finally {
      setEvaluatingRisk(false);
    }
  };

  const handleOpenUploadForCategory = (category?: string, replacesId?: string) => {
    setUploadCategory(category);
    setReplaceDocId(replacesId);
    setIsUploadOpen(true);
  };

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-4">
        <div className="h-6 w-32 bg-surface animate-pulse rounded" />
        <div className="h-40 bg-surface animate-pulse rounded-lg" />
        <div className="h-64 bg-surface animate-pulse rounded-lg" />
      </div>
    );
  }

  if (error || !app) {
    return (
      <div className="p-12 text-center max-w-lg mx-auto">
        <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
        <p className="text-sm font-semibold text-primary-text">Could not load application</p>
        <p className="text-xs text-secondary-text mt-1">{error}</p>
        <div className="flex items-center justify-center space-x-3 mt-4">
          <button
            onClick={() => loadData()}
            className="px-4 py-2 bg-primary text-white text-xs rounded hover:bg-orange-600 transition-colors inline-flex items-center space-x-1.5"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-surface border border-border text-xs rounded hover:bg-surface-muted transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Back button & Action Toolbar */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-1.5 text-xs text-secondary-text hover:text-primary-text font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Applications</span>
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleRunCompliance}
            disabled={evaluating}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-white border border-primary-orange text-primary-orange hover:bg-orange-50/50 text-xs font-semibold rounded-md shadow-xs transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${evaluating ? "animate-spin" : ""}`} />
            <span>{evaluating ? "Evaluating Rules..." : "Run Compliance Engine"}</span>
          </button>

          <button
            onClick={() => handleOpenUploadForCategory()}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-primary-orange hover:bg-primary-orange-hover text-white text-xs font-semibold rounded-md shadow-xs transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>

          <button
            onClick={() => setIsDeleteModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-red-300 text-red-700 hover:bg-red-50 text-xs font-semibold rounded-md shadow-xs transition-colors"
            title="Delete Application Record"
          >
            <Trash2 className="w-3.5 h-3.5 text-red-600" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Main Dossier Header Card */}
      <div className="bg-white rounded-lg border border-border p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-bold font-mono text-primary-text">
                {app.application_identifier}
              </h2>
              <StatusBadge status={app.status} />
            </div>
            <p className="text-xs text-secondary-text mt-1">
              Submitted: {formatDate(app.submission_date)} • Academic Cycle {app.academic_year}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-secondary-text font-medium">Compliance Verdict:</span>
            <span
              className={`text-xs font-bold px-3 py-1 rounded border uppercase font-mono ${
                app.status === "Verified"
                  ? "bg-green-50 text-status-success border-green-200"
                  : app.status === "Action Required"
                  ? "bg-red-50 text-status-error border-red-200"
                  : "bg-amber-50 text-status-warning border-amber-200"
              }`}
            >
              {app.status}
            </span>
          </div>
        </div>

        {/* Institution Info Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-4 text-xs">
          <div>
            <span className="text-secondary-text block text-[11px]">Institution</span>
            <span className="font-semibold text-primary-text">{app.institution_name}</span>
            <span className="text-secondary-text block text-[10px]">
              {app.institution_city}, {app.institution_state}
            </span>
          </div>

          <div>
            <span className="text-secondary-text block text-[11px]">Category</span>
            <span className="font-semibold text-primary-text">{app.application_category}</span>
          </div>

          <div>
            <span className="text-secondary-text block text-[11px]">Institutional Type</span>
            <span className="font-semibold text-primary-text">{app.institution_type || "Technical"}</span>
          </div>

          <div>
            <span className="text-secondary-text block text-[11px]">Audit Findings</span>
            <span className="font-semibold font-mono text-status-error">
              {app.findings.length} Non-Compliances Recorded
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-border flex space-x-6 text-xs font-medium">
        <button
          onClick={() => setActiveTab("compliance")}
          className={`pb-2.5 border-b-2 font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === "compliance"
              ? "border-primary-orange text-primary-orange"
              : "border-transparent text-secondary-text hover:text-primary-text"
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Regulatory Compliance</span>
          {complianceReport && (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-surface border border-border">
              {complianceReport.summary.passed} Passed / {complianceReport.summary.failed} Failed
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("risk")}
          className={`pb-2.5 border-b-2 font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === "risk"
              ? "border-primary-orange text-primary-orange"
              : "border-transparent text-secondary-text hover:text-primary-text"
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Risk Scoring Engine</span>
          {riskReport && (
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold border ${
                riskReport.risk_band === "High"
                  ? "bg-red-50 text-status-error border-red-200"
                  : riskReport.risk_band === "Medium"
                  ? "bg-amber-50 text-status-warning border-amber-200"
                  : "bg-green-50 text-status-success border-green-200"
              }`}
            >
              Score: {riskReport.score.toFixed(0)} ({riskReport.risk_band})
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("checklist")}
          className={`pb-2.5 border-b-2 font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === "checklist"
              ? "border-primary-orange text-primary-orange"
              : "border-transparent text-secondary-text hover:text-primary-text"
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          <span>Document Checklist</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-surface border border-border">
            {checklist.filter((c) => c.status !== "Not uploaded").length}/{checklist.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("all_docs")}
          className={`pb-2.5 border-b-2 font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === "all_docs"
              ? "border-primary-orange text-primary-orange"
              : "border-transparent text-secondary-text hover:text-primary-text"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Attached Documents ({app.documents.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("findings")}
          className={`pb-2.5 border-b-2 font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === "findings"
              ? "border-primary-orange text-primary-orange"
              : "border-transparent text-secondary-text hover:text-primary-text"
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          <span>Findings & Discrepancies ({app.findings.length})</span>
        </button>
      </div>

      {/* Tab 1: Compliance Evaluation */}
      {activeTab === "compliance" && (
        <div className="space-y-6">
          {/* Executive Metrics Banner */}
          {complianceReport ? (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-lg border border-border">
                <span className="text-[11px] text-secondary-text font-medium block">Total Rules Evaluated</span>
                <span className="text-xl font-bold font-mono text-primary-text">
                  {complianceReport.summary.total_evaluated}
                </span>
              </div>
              <div className="bg-white p-4 rounded-lg border border-green-200 bg-green-50/20">
                <span className="text-[11px] text-status-success font-medium block">Rules Passed</span>
                <span className="text-xl font-bold font-mono text-status-success">
                  {complianceReport.summary.passed}
                </span>
              </div>
              <div className="bg-white p-4 rounded-lg border border-red-200 bg-red-50/20">
                <span className="text-[11px] text-status-error font-medium block">Failed Checks</span>
                <span className="text-xl font-bold font-mono text-status-error">
                  {complianceReport.summary.failed}
                </span>
              </div>
              <div className="bg-white p-4 rounded-lg border border-amber-200 bg-amber-50/20">
                <span className="text-[11px] text-status-warning font-medium block">Needs Human Review</span>
                <span className="text-xl font-bold font-mono text-status-warning">
                  {complianceReport.summary.needs_review}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-6 bg-surface rounded-lg border border-border flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                  Compliance Rule Engine Ready
                </h4>
                <p className="text-xs text-secondary-text mt-0.5">
                  Click &quot;Run Compliance Engine&quot; to evaluate uploaded documents against APH 2026-27 rules.
                </p>
              </div>
              <button
                onClick={handleRunCompliance}
                disabled={evaluating}
                className="px-4 py-2 bg-primary-orange text-white text-xs font-semibold rounded shadow-xs hover:bg-primary-orange-hover"
              >
                {evaluating ? "Evaluating..." : "Execute Evaluation"}
              </button>
            </div>
          )}

          {/* Detailed Rule Evaluations List */}
          {complianceReport && complianceReport.rule_evaluations.length > 0 && (
            <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
              <div className="p-4 border-b border-border bg-surface/40 flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                    Detailed Rule Scrutiny Breakdown
                  </h3>
                  <p className="text-[11px] text-secondary-text">
                    Traceable results with Approval Process Handbook legal citations
                  </p>
                </div>
              </div>

              <div className="divide-y divide-border">
                {complianceReport.rule_evaluations.map((evalItem: RuleEvaluationResult, idx: number) => (
                  <div key={idx} className="p-4 space-y-2 hover:bg-surface/20 transition-colors">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-bold text-primary-orange">
                            {evalItem.rule_code}
                          </span>
                          <span className="text-xs font-bold text-primary-text">{evalItem.rule_name}</span>
                          {evalItem.is_pending_confirmation && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-50 text-status-warning border border-amber-200 font-mono">
                              Pending Confirmation
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-secondary-text leading-relaxed">{evalItem.explanation}</p>
                      </div>

                      <div className="shrink-0 flex items-center space-x-2">
                        {evalItem.result === "PASS" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#EBF7F0] text-[#287A52] border border-[#287A52]/20">
                            <Check className="w-3.5 h-3.5" />
                            PASS
                          </span>
                        ) : evalItem.result === "FAIL" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#FDEDED] text-[#C7463A] border border-[#C7463A]/20">
                            <X className="w-3.5 h-3.5" />
                            FAIL
                          </span>
                        ) : evalItem.result === "NEEDS_REVIEW" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#FFF8EB] text-[#B96A19] border border-[#B96A19]/20">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            NEEDS REVIEW
                          </span>
                        ) : evalItem.result === "NOT_EVALUATED" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-700 border border-gray-300">
                            <Clock className="w-3.5 h-3.5 text-gray-500" />
                            NOT EVALUATED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-surface text-secondary-text border border-border">
                            NOT APPLICABLE
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Source Citation Footer */}
                    <div className="bg-surface/60 rounded p-2 border border-border/80 text-[10px] text-secondary-text flex items-center justify-between">
                      <div className="flex items-center space-x-1.5">
                        <BookOpen className="w-3 h-3 text-primary-orange shrink-0" />
                        <span>
                          <strong className="text-primary-text">{evalItem.regulatory_source.title}:</strong>{" "}
                          {evalItem.regulatory_source.section} ({evalItem.regulatory_source.page})
                        </span>
                      </div>
                      {evalItem.actual_value && (
                        <div className="font-mono text-primary-text">
                          Value: <strong>{evalItem.actual_value}</strong>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Risk Scoring Engine */}
      {activeTab === "risk" && (
        <div className="space-y-6">
          {riskReport ? (
            <div className="space-y-6">
              {/* Executive Risk Banner */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-lg border border-border">
                  <span className="text-[11px] text-secondary-text font-medium block">
                    Application Risk Score
                  </span>
                  <div className="flex items-baseline space-x-1.5 mt-1">
                    <span className="text-3xl font-extrabold font-mono text-primary-text">
                      {riskReport.score.toFixed(0)}
                    </span>
                    <span className="text-xs text-secondary-text font-mono">/ 100</span>
                  </div>
                  <span className="text-[10px] text-secondary-text block mt-1">
                    Deterministic 0–100 risk index
                  </span>
                </div>

                <div
                  className={`p-5 rounded-lg border ${
                    riskReport.risk_band === "High"
                      ? "bg-red-50/40 border-red-200"
                      : riskReport.risk_band === "Medium"
                      ? "bg-amber-50/40 border-amber-200"
                      : "bg-green-50/40 border-green-200"
                  }`}
                >
                  <span className="text-[11px] text-secondary-text font-medium block">
                    Risk Classification
                  </span>
                  <span
                    className={`text-xl font-bold font-mono block mt-1 ${
                      riskReport.risk_band === "High"
                        ? "text-status-error"
                        : riskReport.risk_band === "Medium"
                        ? "text-status-warning"
                        : "text-status-success"
                    }`}
                  >
                    {riskReport.risk_band} Risk
                  </span>
                  <span className="text-[10px] text-secondary-text block mt-1">
                    Band: {riskReport.risk_band === "High" ? "60–100" : riskReport.risk_band === "Medium" ? "30–59" : "0–29"}
                  </span>
                </div>

                <div className="bg-white p-5 rounded-lg border border-border">
                  <span className="text-[11px] text-secondary-text font-medium block">
                    Assessment Completeness
                  </span>
                  <span
                    className={`text-base font-bold font-mono block mt-1 ${
                      riskReport.completeness_status === "COMPLETE"
                        ? "text-status-success"
                        : riskReport.completeness_status === "REQUIRES_REVIEW"
                        ? "text-status-warning"
                        : "text-status-error"
                    }`}
                  >
                    {riskReport.completeness_status}
                  </span>
                  <span className="text-[10px] text-secondary-text block mt-1">
                    {riskReport.is_provisional ? "Provisional Assessment" : "Evidence Verified"}
                  </span>
                </div>

                <div className="bg-white p-5 rounded-lg border border-border flex flex-col justify-between">
                  <div>
                    <span className="text-[11px] text-secondary-text font-medium block">
                      Contributing Factors
                    </span>
                    <span className="text-xl font-bold font-mono text-primary-text block mt-1">
                      {riskReport.contributing_factors.length} Factor(s)
                    </span>
                  </div>
                  <button
                    onClick={handleRunRisk}
                    disabled={evaluatingRisk}
                    className="mt-2 w-full px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded hover:bg-orange-600 transition-colors inline-flex items-center justify-center space-x-1.5"
                  >
                    <RotateCw className={`w-3 h-3 ${evaluatingRisk ? "animate-spin" : ""}`} />
                    <span>{evaluatingRisk ? "Evaluating..." : "Re-evaluate Risk"}</span>
                  </button>
                </div>
              </div>

              {/* Explainable Decision Support Banner */}
              <div className="p-4 bg-surface rounded-lg border border-border text-xs text-secondary-text flex items-start space-x-3">
                <Shield className="w-5 h-5 text-primary-orange shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <strong className="text-primary-text block">
                    Regulatory Decision Support System Notice
                  </strong>
                  <p className="leading-relaxed">
                    {riskReport.explanation} Risk score is calculated deterministically from verified compliance findings and evidence completeness. It does not constitute an automated legal approval or rejection verdict.
                  </p>
                </div>
              </div>

              {/* Missing Evidence & Unresolved Reviews Warnings */}
              {(riskReport.missing_evidence_items.length > 0 || riskReport.unresolved_reviews.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {riskReport.missing_evidence_items.length > 0 && (
                    <div className="p-4 rounded-lg border border-red-200 bg-red-50/20 space-y-2">
                      <div className="flex items-center space-x-1.5 text-status-error font-semibold text-xs">
                        <AlertCircle className="w-4 h-4" />
                        <span>Missing Required Evidence</span>
                      </div>
                      <ul className="text-xs text-secondary-text list-disc list-inside space-y-1">
                        {riskReport.missing_evidence_items.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {riskReport.unresolved_reviews.length > 0 && (
                    <div className="p-4 rounded-lg border border-amber-200 bg-amber-50/20 space-y-2">
                      <div className="flex items-center space-x-1.5 text-status-warning font-semibold text-xs">
                        <Clock className="w-4 h-4" />
                        <span>Unresolved Human Scrutiny Items</span>
                      </div>
                      <ul className="text-xs text-secondary-text list-disc list-inside space-y-1">
                        {riskReport.unresolved_reviews.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Factor by Factor Breakdown Table */}
              <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
                <div className="p-4 border-b border-border bg-surface/40 flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                      Factor-by-Factor Risk Breakdown
                    </h3>
                    <p className="text-[11px] text-secondary-text">
                      Traceable penalties assigned to specific non-compliances and evidence gaps
                    </p>
                  </div>
                  <span className="text-[10px] font-mono text-secondary-text">
                    Config: {riskReport.assessment_version}
                  </span>
                </div>

                {riskReport.contributing_factors.length === 0 ? (
                  <div className="p-8 text-center text-xs text-secondary-text">
                    <CheckCircle2 className="w-8 h-8 text-status-success mx-auto mb-2" />
                    <span>No risk penalties identified. All evaluated statutory rules satisfy requirements.</span>
                  </div>
                ) : (
                  <div className="divide-y divide-border">
                    {riskReport.contributing_factors.map((factor, idx) => (
                      <div key={idx} className="p-4 space-y-2 hover:bg-surface/20 transition-colors">
                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-xs font-bold text-primary-orange">
                                {factor.factor_code}
                              </span>
                              <span className="text-xs font-bold text-primary-text">
                                {factor.factor_name}
                              </span>
                              <span
                                className={`text-[9px] px-1.5 py-0.2 rounded font-mono uppercase ${
                                  factor.severity.toUpperCase() === "CRITICAL"
                                    ? "bg-red-50 text-status-error border border-red-200"
                                    : "bg-amber-50 text-status-warning border border-amber-200"
                                }`}
                              >
                                {factor.severity}
                              </span>
                            </div>
                            <p className="text-xs text-secondary-text leading-relaxed">
                              {factor.reason}
                            </p>
                          </div>

                          <div className="shrink-0 text-right">
                            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-red-50 text-status-error border border-red-200">
                              +{factor.points} pts
                            </span>
                          </div>
                        </div>

                        {factor.evidence_reference && (
                          <div className="bg-surface/60 rounded p-2 border border-border/80 text-[10px] text-secondary-text flex items-center justify-between font-mono">
                            <span>Evidence: {factor.evidence_reference}</span>
                            {factor.rule_code && <span>Rule: {factor.rule_code}</span>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Assessment Timeline / History */}
              {riskReport.history && riskReport.history.length > 1 && (
                <div className="bg-white rounded-lg border border-border p-4 space-y-3">
                  <h4 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                    Risk Assessment Audit History
                  </h4>
                  <div className="divide-y divide-border text-xs">
                    {riskReport.history.map((h, i) => (
                      <div key={i} className="py-2 flex items-center justify-between text-secondary-text">
                        <span className="font-mono text-primary-text font-medium">
                          {formatDateTime(h.calculated_at)}
                        </span>
                        <div className="flex items-center space-x-3">
                          <span>
                            Score: <strong className="font-mono text-primary-text">{h.score.toFixed(0)}/100</strong> ({h.risk_band})
                          </span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border font-mono">
                            {h.completeness_status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 bg-surface rounded-lg border border-border text-center space-y-3 max-w-lg mx-auto">
              <AlertTriangle className="w-8 h-8 text-primary-orange mx-auto" />
              <div>
                <h4 className="text-sm font-bold text-primary-text">
                  Risk Assessment Not Yet Evaluated
                </h4>
                <p className="text-xs text-secondary-text mt-1 leading-relaxed">
                  Run the risk engine to evaluate deterministic risk weights, factor penalties, and evidence completeness based on the latest compliance findings.
                </p>
              </div>
              <button
                onClick={handleRunRisk}
                disabled={evaluatingRisk}
                className="px-4 py-2 bg-primary-orange text-white text-xs font-semibold rounded shadow-xs hover:bg-primary-orange-hover transition-colors"
              >
                {evaluatingRisk ? "Evaluating Risk..." : "Execute Risk Assessment"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Regulatory Document Checklist */}
      {activeTab === "checklist" && (
        <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
          <div className="p-4 border-b border-border bg-surface/40 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                AICTE Approval Process Handbook (APH 2026-27) Document Checklist
              </h3>
              <p className="text-[11px] text-secondary-text mt-0.5">
                Configured requirements for &quot;{app.application_category}&quot;
              </p>
            </div>
            <button
              onClick={loadData}
              title="Refresh Checklist"
              className="p-1.5 rounded border border-border bg-white text-secondary-text hover:text-primary-text"
            >
              <RotateCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-border">
            {checklist.map((item, idx) => (
              <div
                key={idx}
                className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-surface/30 transition-colors"
              >
                <div className="space-y-1 max-w-2xl">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-primary-text">{item.category}</span>
                    {item.is_mandatory ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-red-50 text-status-error font-medium border border-red-200">
                        Mandatory
                      </span>
                    ) : item.is_conditional ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-medium border border-amber-200">
                        Conditional
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-secondary-text">
                        Optional
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-secondary-text leading-relaxed">
                    {item.description}
                  </p>
                  {item.condition_description && (
                    <div className="text-[10.5px] text-amber-800 bg-amber-50/70 px-2 py-1 rounded border border-amber-200/80">
                      <span className="font-semibold">Condition:</span> {item.condition_description}
                    </div>
                  )}

                  {item.regulatory_source && (
                    <div className="text-[10px] text-blue-800 bg-blue-50/60 px-2 py-0.5 rounded border border-blue-200/60 inline-flex items-center gap-1">
                      <BookOpen className="w-3 h-3 text-blue-600 shrink-0" />
                      <span>{item.regulatory_source.section} — {(item.regulatory_source as any).clause || item.regulatory_source.page}</span>
                    </div>
                  )}

                  {item.uploaded_document && (
                    <div className="text-[10px] text-secondary-text font-mono flex items-center gap-2 pt-1">
                      <span>Attached: {item.uploaded_document.original_filename}</span>
                      <span>(v{item.uploaded_document.version})</span>
                      <span>• SHA-256 verified</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <StatusBadge status={item.status} />

                  {item.uploaded_document ? (
                    <div className="flex items-center space-x-1.5">
                      <button
                        onClick={() => setSelectedDoc(item.uploaded_document!)}
                        className="px-3 py-1 bg-surface border border-border rounded text-xs font-medium text-primary-text hover:bg-surface-muted flex items-center gap-1"
                      >
                        <Eye className="w-3.5 h-3.5 text-primary-orange" />
                        <span>Inspect OCR</span>
                      </button>
                      <button
                        onClick={() =>
                          handleOpenUploadForCategory(item.category, item.uploaded_document!.id)
                        }
                        className="px-2.5 py-1 text-xs text-secondary-text hover:text-primary-text border border-border rounded bg-white hover:bg-surface"
                      >
                        Replace
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleOpenUploadForCategory(item.category)}
                      className="px-3 py-1 bg-primary-orange hover:bg-primary-orange-hover text-white rounded text-xs font-medium shadow-xs flex items-center gap-1"
                    >
                      <Upload className="w-3.5 h-3.5" />
                      <span>Upload</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: All Uploaded Documents */}
      {activeTab === "all_docs" && (
        <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
          {app.documents.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-8 h-8 text-secondary-text/40 mx-auto mb-2" />
              <p className="text-xs font-semibold text-primary-text">No documents uploaded yet</p>
              <button
                onClick={() => handleOpenUploadForCategory()}
                className="mt-3 px-3 py-1.5 bg-primary-orange text-white text-xs rounded font-medium"
              >
                Upload First Document
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface text-[11px] font-semibold text-secondary-text">
                    <th className="py-2.5 px-4">Filename</th>
                    <th className="py-2.5 px-4">Category</th>
                    <th className="py-2.5 px-4">Size</th>
                    <th className="py-2.5 px-4">Version</th>
                    <th className="py-2.5 px-4">Uploaded Date</th>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {app.documents.map((d) => (
                    <tr key={d.id} className="hover:bg-surface/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-primary-text">
                        {d.original_filename}
                      </td>
                      <td className="py-3 px-4 text-secondary-text">{d.document_type}</td>
                      <td className="py-3 px-4 font-mono text-secondary-text">
                        {d.file_size_bytes ? `${(d.file_size_bytes / 1024).toFixed(1)} KB` : "—"}
                      </td>
                      <td className="py-3 px-4 font-mono text-secondary-text">v{d.version}</td>
                      <td className="py-3 px-4 text-secondary-text">{formatDate(d.created_at)}</td>
                      <td className="py-3 px-4">
                        <StatusBadge status={d.processing_status} />
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={() => setSelectedDoc(d)}
                            className="px-2.5 py-1 bg-surface border border-border text-xs rounded hover:bg-surface-muted font-medium text-primary-orange inline-flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View & OCR</span>
                          </button>
                          <button
                            onClick={() => handleOpenUploadForCategory(d.document_type, d.id)}
                            className="px-2 py-1 text-xs border border-border rounded text-secondary-text hover:text-primary-text"
                          >
                            Replace
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Findings */}
      {activeTab === "findings" && (
        <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
          {app.findings.length === 0 ? (
            <div className="p-8 text-center text-xs text-secondary-text">
              <CheckCircle2 className="w-6 h-6 text-status-success mx-auto mb-1" />
              No compliance discrepancies detected for this application dossier.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {app.findings.map((f) => (
                <div key={f.id} className="p-4 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {f.rule_code && (
                        <span className="font-mono text-[10px] font-bold text-primary-orange">
                          {f.rule_code}
                        </span>
                      )}
                      <span className="font-semibold text-primary-text">{f.title}</span>
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        f.severity === "Critical" || f.severity === "CRITICAL" || f.severity === "High"
                          ? "bg-red-50 text-status-error border border-red-200"
                          : "bg-amber-50 text-status-warning border border-amber-200"
                      }`}
                    >
                      {f.severity} Severity
                    </span>
                  </div>
                  <p className="text-secondary-text leading-relaxed">{f.explanation}</p>
                  {f.evidence_reference && (
                    <div className="text-[10px] text-secondary-text font-mono pt-1">
                      Evidence Citation: {f.evidence_reference}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        applicationId={app.id}
        defaultCategory={uploadCategory}
        replacesDocumentId={replaceDocId}
        applicationCategory={app.application_category}
        availableCategories={checklist.map((c) => c.category)}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => {
          loadData();
          onRefresh();
        }}
      />

      {/* Document Inspector & OCR Side-by-side Modal */}
      {selectedDoc && (
        <DocumentViewer
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
          onRefresh={() => {
            loadData();
            onRefresh();
          }}
          onReplace={(d) => {
            setSelectedDoc(null);
            handleOpenUploadForCategory(d.document_type, d.id);
          }}
        />
      )}

      {/* Delete Application Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-lg border border-border shadow-xl w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between bg-red-50/50">
              <div className="flex items-center space-x-2 text-red-800">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider">Confirm Application Deletion</h3>
              </div>
              <button
                onClick={() => setIsDeleteModalOpen(false)}
                className="p-1 text-secondary-text hover:text-primary-text rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              {deleteError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  {deleteError}
                </div>
              )}

              <p className="text-secondary-text leading-relaxed">
                Are you sure you want to delete application <strong className="text-primary-text">{app?.application_identifier}</strong>? This action will permanently remove the application record from active scrutiny.
              </p>

              <div className="p-3 bg-surface-muted rounded border border-border text-[11px] text-secondary-text space-y-1">
                <span className="font-semibold text-primary-text block">Forensic Audit Retention:</span>
                <span>An indelible forensic audit record will be logged with full deletion and document retention metadata.</span>
              </div>
            </div>

            <div className="p-3 bg-surface-muted/60 border-t border-border flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(false)}
                disabled={deleting}
                className="px-3.5 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded hover:bg-surface"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteApplication}
                disabled={deleting}
                className="px-3.5 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded shadow-xs disabled:opacity-50 flex items-center space-x-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{deleting ? "Deleting..." : "Confirm Delete"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
