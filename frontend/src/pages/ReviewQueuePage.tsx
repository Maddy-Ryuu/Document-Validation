import React, { useState, useEffect } from "react";
import {
  ListTodo,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RotateCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Shield,
  UserCheck,
  Check,
  X,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";
import { QueueItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../lib/utils";

interface ReviewQueuePageProps {
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const ReviewQueuePage: React.FC<ReviewQueuePageProps> = ({
  onSelectApplication,
  refreshTrigger,
}) => {
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status transition feedback
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchQueue();
  }, [page, statusFilter, priorityFilter, refreshTrigger]);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getReviewQueue({
        page,
        limit: 10,
        search: search.trim() || undefined,
        status: statusFilter !== "All" ? statusFilter : undefined,
        priority: priorityFilter !== "All" ? priorityFilter : undefined,
      });
      setQueueItems(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      setError(err.message || "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQueue();
  };

  const handleStatusTransition = async (appId: string, newStatus: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setUpdatingId(appId);
    try {
      await api.updateApplication(appId, { status: newStatus as any });
      setActionSuccess(`Application status transitioned to "${newStatus}"`);
      setTimeout(() => setActionSuccess(null), 3500);
      fetchQueue();
    } catch (err: any) {
      alert(`Status transition failed: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  const highPriorityCount = queueItems.filter((item) => item.priority === "High").length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-primary-text tracking-tight">Scrutiny Officer Review Queue</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200 rounded">
              Prioritized Worklist
            </span>
          </div>
          <p className="text-xs text-secondary-text mt-0.5">
            Active worklist of regulatory applications requiring officer review, defect resolution, or committee sign-off
          </p>
        </div>

        <button
          onClick={fetchQueue}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
        >
          <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Applications in Worklist</span>
            <ListTodo className="w-4 h-4 text-primary-orange" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">{total}</div>
          <div className="text-[11px] text-secondary-text mt-1">Pending scrutiny or formal decision</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">High Priority Cases</span>
            <AlertTriangle className="w-4 h-4 text-red-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-red-600">{highPriorityCount}</div>
          <div className="text-[11px] text-secondary-text mt-1">High risk band or open compliance defects</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Assigned Scrutiny Desk</span>
            <UserCheck className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">AICTE Central</div>
          <div className="text-[11px] text-secondary-text mt-1">Approval Bureau, New Delhi</div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md w-full">
          <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search application identifier, institution, city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <select
            value={priorityFilter}
            onChange={(e) => {
              setPriorityFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Priorities</option>
            <option value="High">High Priority</option>
            <option value="Medium">Medium Priority</option>
            <option value="Low">Low Priority</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Queue Statuses</option>
            <option value="Action Required">Action Required</option>
            <option value="Under Validation">Under Validation</option>
          </select>
        </div>
      </div>

      {/* Queue Table */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
            <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
            <span>Loading scrutiny worklist...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <span>{error}</span>
          </div>
        ) : queueItems.length === 0 ? (
          <div className="p-12 text-center text-secondary-text text-xs">
            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
            <p className="font-medium text-primary-text">Review Queue is Clear</p>
            <p className="mt-1">All applications have been processed or moved to final states.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-muted/50 text-[11px] font-semibold text-secondary-text uppercase tracking-wider">
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Application</th>
                  <th className="py-3 px-4">Institution & Location</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4">Status & Documents</th>
                  <th className="py-3 px-4 text-right">Quick Decision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {queueItems.map((item) => {
                  const isUpdating = updatingId === item.id;
                  return (
                    <tr
                      key={item.id}
                      onClick={() => onSelectApplication(item.id)}
                      className="hover:bg-surface/50 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider ${
                            item.priority === "High"
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : item.priority === "Medium"
                              ? "bg-amber-50 text-amber-700 border border-amber-200"
                              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          }`}
                        >
                          {item.priority}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-semibold text-primary-orange">
                        {item.application_identifier}
                        <div className="text-[10px] text-secondary-text font-normal mt-0.5">
                          {item.application_category} • {item.academic_year}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-medium text-primary-text truncate max-w-xs">{item.institution_name}</div>
                        <div className="text-[11px] text-secondary-text">
                          {item.institution_city}, {item.institution_state}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              item.risk_band === "High" || item.risk_band === "Extreme"
                                ? "bg-red-500"
                                : item.risk_band === "Medium"
                                ? "bg-amber-500"
                                : item.risk_band === "Low"
                                ? "bg-emerald-500"
                                : "bg-gray-400"
                            }`}
                          />
                          <span className="font-medium text-primary-text">
                            {item.risk_band || "Unevaluated"}
                          </span>
                          {item.risk_score !== null && item.risk_score !== undefined && (
                            <span className="text-[10px] text-secondary-text">({item.risk_score}/100)</span>
                          )}
                        </div>
                        {item.findings_count > 0 && (
                          <div className="text-[10px] text-red-600 mt-0.5">
                            {item.findings_count} finding(s) pending
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge status={item.status} />
                        <div className="text-[10px] text-secondary-text mt-1">
                          {item.documents_count} document(s) uploaded
                        </div>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          {item.status !== "Verified" && (
                            <button
                              disabled={isUpdating}
                              onClick={(e) => handleStatusTransition(item.id, "Verified", e)}
                              className="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 rounded text-[11px] font-medium transition-colors"
                              title="Sign-off as Verified"
                            >
                              Verify
                            </button>
                          )}

                          {item.status !== "Action Required" && (
                            <button
                              disabled={isUpdating}
                              onClick={(e) => handleStatusTransition(item.id, "Action Required", e)}
                              className="px-2 py-1 bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 rounded text-[11px] font-medium transition-colors"
                              title="Flag as Action Required"
                            >
                              Deficiency
                            </button>
                          )}

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectApplication(item.id);
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
        {!loading && queueItems.length > 0 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-xs text-secondary-text">
            <span>
              Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, total)} of {total} queue items
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
