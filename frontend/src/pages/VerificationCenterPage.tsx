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
} from "lucide-react";
import { api } from "../services/api";
import { ApplicationListItem, RiskAssessmentReport } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../lib/utils";

interface VerificationCenterPageProps {
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const VerificationCenterPage: React.FC<VerificationCenterPageProps> = ({
  onSelectApplication,
  refreshTrigger,
}) => {
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

  useEffect(() => {
    fetchApplications();
  }, [page, statusFilter, refreshTrigger]);

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
            Consolidated regulatory rule verification, statutory evidence matching, and explainable risk scores
          </p>
        </div>

        <button
          onClick={fetchApplications}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
        >
          <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
          <span>Refresh</span>
        </button>
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
              Approval Process Handbook (APH 2026-27) Verification Engine
            </h3>
            <p className="text-xs text-secondary-text mt-0.5 max-w-2xl">
              Deterministic rule evaluation covers Fire Safety NOC, Land Norms & Non-Encumbrance, Built-Up Area Sanction, Faculty Cadre Ratios, and Cryptographic Document Hash Tampering.
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
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {applications.map((app) => {
                  const isRerunning = rerunningId === app.id;
                  return (
                    <tr
                      key={app.id}
                      onClick={() => onSelectApplication(app.id)}
                      className="hover:bg-surface/50 cursor-pointer transition-colors"
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
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            disabled={isRerunning}
                            onClick={(e) => handleRerunVerification(app.id, e)}
                            className="flex items-center space-x-1 px-2.5 py-1 bg-white border border-border text-primary-text hover:bg-surface rounded text-xs font-medium shadow-xs transition-colors"
                            title="Rerun Regulatory Rule Engine"
                          >
                            <Play className={`w-3 h-3 text-primary-orange ${isRerunning ? "animate-spin" : ""}`} />
                            <span>{isRerunning ? "Evaluating..." : "Run Engine"}</span>
                          </button>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectApplication(app.id);
                            }}
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
    </div>
  );
};
