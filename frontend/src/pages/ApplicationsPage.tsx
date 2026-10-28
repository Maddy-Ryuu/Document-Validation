import React, { useState, useEffect } from "react";
import {
  FileText,
  Search,
  Filter,
  Plus,
  RotateCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Trash2,
  AlertTriangle,
  X,
  CheckCircle2,
} from "lucide-react";
import { api } from "../services/api";
import { ApplicationListItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../lib/utils";

interface ApplicationsPageProps {
  onOpenNewAppModal: () => void;
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const ApplicationsPage: React.FC<ApplicationsPageProps> = ({
  onOpenNewAppModal,
  onSelectApplication,
  refreshTrigger,
}) => {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All");
  const [category, setCategory] = useState("All");
  const [academicYear, setAcademicYear] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Deletion modal state
  const [appToDelete, setAppToDelete] = useState<ApplicationListItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const confirmDelete = async () => {
    if (!appToDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteApplication(appToDelete.id);
      setActionFeedback(`Application ${appToDelete.application_identifier} deleted successfully. Forensic audit record preserved.`);
      setAppToDelete(null);
      fetchApps();
    } catch (err: any) {
      setDeleteError(err.message || "Failed to delete application");
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, [page, status, category, academicYear, refreshTrigger]);

  const fetchApps = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getApplications({
        page,
        limit: 12,
        search: search.trim() || undefined,
        status,
        category,
        academic_year: academicYear,
      });
      setApplications(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      setError(err.message || "Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchApps();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h2 className="text-2xl font-bold text-primary-text tracking-tight">Applications Registry</h2>
          <p className="text-xs text-secondary-text mt-0.5">
            Full repository of submitted AICTE institutional approval dossiers
          </p>
        </div>

        <button
          onClick={onOpenNewAppModal}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-primary-orange hover:bg-primary-orange-hover text-white text-xs font-medium rounded-md shadow-xs transition-colors self-start md:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Application</span>
        </button>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-xs flex items-center justify-between animate-in fade-in">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionFeedback}</span>
          </div>
          <button onClick={() => setActionFeedback(null)} className="p-0.5 hover:bg-emerald-100 rounded">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filter / Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by application ID, institution name, or city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="text-xs bg-white border border-border rounded-md px-2.5 py-1.5 text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Statuses</option>
            <option value="Under Validation">Under Validation</option>
            <option value="Action Required">Action Required</option>
            <option value="Verified">Verified</option>
            <option value="Approved">Approved</option>
          </select>

          {/* Category Filter */}
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="text-xs bg-white border border-border rounded-md px-2.5 py-1.5 text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Categories</option>
            <option value="Extension of Approval (EoA)">Extension of Approval</option>
            <option value="Increase in Intake">Increase in Intake</option>
            <option value="New Institute">New Institute</option>
          </select>

          {/* Academic Year Filter */}
          <select
            value={academicYear}
            onChange={(e) => {
              setAcademicYear(e.target.value);
              setPage(1);
            }}
            className="text-xs bg-white border border-border rounded-md px-2.5 py-1.5 text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Years</option>
            <option value="2026-2027">2026-2027</option>
            <option value="2027-2028">2027-2028</option>
          </select>

          <button
            onClick={fetchApps}
            title="Refresh"
            className="p-1.5 bg-white border border-border rounded-md text-secondary-text hover:text-primary-text hover:bg-surface transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 bg-surface animate-pulse rounded" />
            ))}
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-status-error">
            <p>{error}</p>
            <button
              onClick={fetchApps}
              className="mt-2 px-3 py-1 bg-surface text-primary-text border border-border rounded text-xs"
            >
              Retry
            </button>
          </div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-8 h-8 text-secondary-text/40 mx-auto mb-2" />
            <p className="text-xs font-semibold text-primary-text">No applications match your filter</p>
            <p className="text-[11px] text-secondary-text mt-0.5">
              Reset search filters or create a new application
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface text-[11px] font-semibold text-secondary-text">
                  <th className="py-2.5 px-4">Application ID</th>
                  <th className="py-2.5 px-4">Institution Name</th>
                  <th className="py-2.5 px-4">Category</th>
                  <th className="py-2.5 px-4">Academic Year</th>
                  <th className="py-2.5 px-4">Submitted Date</th>
                  <th className="py-2.5 px-4">Documents</th>
                  <th className="py-2.5 px-4">Findings</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {applications.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => onSelectApplication(app.id)}
                    className="hover:bg-surface/50 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-primary-text">
                      {app.application_identifier}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-primary-text">{app.institution_name}</div>
                      <div className="text-[10px] text-secondary-text">
                        {app.institution_city}, {app.institution_state}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-secondary-text">{app.application_category}</td>
                    <td className="py-3 px-4 font-mono text-secondary-text">{app.academic_year}</td>
                    <td className="py-3 px-4 text-secondary-text">{formatDate(app.submission_date)}</td>
                    <td className="py-3 px-4 font-mono text-secondary-text">{app.documents_count}</td>
                    <td className="py-3 px-4">
                      {app.findings_count > 0 ? (
                        <span className="text-status-error font-semibold font-mono">{app.findings_count}</span>
                      ) : (
                        <span className="text-secondary-text font-mono">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectApplication(app.id);
                          }}
                          className="text-primary-orange hover:text-primary-orange-hover font-medium text-[11px]"
                        >
                          Inspect
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setAppToDelete(app);
                          }}
                          title="Delete Application"
                          className="p-1 text-secondary-text hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="p-3 border-t border-border flex items-center justify-between text-xs bg-surface/30">
            <span className="text-secondary-text text-[11px]">
              Page {page} of {pages} ({total} items)
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded border border-border bg-white text-secondary-text hover:text-primary-text disabled:opacity-40"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={page >= pages}
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                className="p-1.5 rounded border border-border bg-white text-secondary-text hover:text-primary-text disabled:opacity-40"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Deletion Confirmation Modal */}
      {appToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-lg border border-border shadow-xl w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between bg-red-50/50">
              <div className="flex items-center space-x-2 text-red-800">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider">Confirm Application Deletion</h3>
              </div>
              <button
                onClick={() => setAppToDelete(null)}
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
                Are you sure you want to delete application <strong className="text-primary-text">{appToDelete.application_identifier}</strong> for <strong className="text-primary-text">{appToDelete.institution_name}</strong>?
              </p>

              <div className="p-3 bg-surface-muted rounded border border-border text-[11px] text-secondary-text space-y-1">
                <span className="font-semibold text-primary-text block">Statutory Audit Retention:</span>
                <span>An indelible forensic audit record will be logged with full deletion metadata. Linked document records are archived according to AICTE compliance retention rules.</span>
              </div>
            </div>

            <div className="p-3 bg-surface-muted/60 border-t border-border flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setAppToDelete(null)}
                disabled={deleting}
                className="px-3.5 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded hover:bg-surface"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
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
