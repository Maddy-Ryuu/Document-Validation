import React, { useState, useEffect } from "react";
import {
  History,
  Search,
  Filter,
  RotateCw,
  Shield,
  Clock,
  Layers,
  ChevronLeft,
  ChevronRight,
  FileText,
  Building,
  CheckCircle2,
  AlertCircle,
  Eye,
} from "lucide-react";
import { api } from "../services/api";
import { AuditEventItem } from "../types";
import { formatDateTime } from "../lib/utils";

interface AuditTrailPageProps {
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const AuditTrailPage: React.FC<AuditTrailPageProps> = ({
  onSelectApplication,
  refreshTrigger,
}) => {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [entityFilter, setEntityFilter] = useState("All");
  const [actionFilter, setActionFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected event detail view
  const [selectedEvent, setSelectedEvent] = useState<AuditEventItem | null>(null);

  useEffect(() => {
    fetchEvents();
  }, [page, entityFilter, actionFilter, refreshTrigger]);

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAuditEvents({
        page,
        limit: 15,
        entity_type: entityFilter !== "All" ? entityFilter : undefined,
        action: actionFilter !== "All" ? actionFilter : undefined,
        search: search.trim() || undefined,
      });
      setEvents(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      setError(err.message || "Failed to load audit trail");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEvents();
  };

  const formatActionName = (act: string) => {
    return act.replace(/_/g, " ").toUpperCase();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-primary-text tracking-tight">Regulatory Audit Trail & Compliance Log</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
              Immutable Ledger
            </span>
          </div>
          <p className="text-xs text-secondary-text mt-0.5">
            Forensic, timestamped record of inspection actions, rule evaluation history, document operations, and reviewer decisions
          </p>
        </div>

        <button
          onClick={fetchEvents}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
        >
          <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
          <span>Refresh Audit Log</span>
        </button>
      </div>

      {/* Security Assurance Banner */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-primary-text">Statutory Non-Repudiation & Audit Integrity</div>
            <div className="text-[11px] text-secondary-text">
              Total {total} verified events recorded in PostgreSQL ledger. Entries are append-only and cannot be altered or removed.
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md w-full">
          <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search action, entity ID, or details..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <select
            value={entityFilter}
            onChange={(e) => {
              setEntityFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Entity Types</option>
            <option value="Application">Application</option>
            <option value="Institution">Institution</option>
            <option value="Document">Document</option>
          </select>

          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="All">All Actions</option>
            <option value="CREATE">Create</option>
            <option value="UPDATE">Update</option>
            <option value="UPLOAD">Upload</option>
            <option value="REVIEW">Review Decisions</option>
            <option value="VERIFICATION">Verification Runs</option>
          </select>
        </div>
      </div>

      {/* Main Audit Table */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
            <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
            <span>Loading audit history from secure ledger...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <span>{error}</span>
          </div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-secondary-text text-xs">
            <History className="w-8 h-8 mx-auto mb-2 text-border" />
            <p className="font-medium text-primary-text">No audit events match filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-muted/50 text-[11px] font-semibold text-secondary-text uppercase tracking-wider">
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">Entity Type</th>
                  <th className="py-3 px-4">Entity Identifier</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Change Summary</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {events.map((ev) => {
                  const isApp = ev.entity_type === "Application";
                  return (
                    <tr key={ev.id} className="hover:bg-surface/50 transition-colors">
                      <td className="py-3 px-4 text-secondary-text text-[11px] font-mono whitespace-nowrap">
                        {formatDateTime(ev.created_at)}
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-semibold rounded ${
                            ev.entity_type === "Application"
                              ? "bg-blue-50 text-blue-700 border border-blue-200"
                              : ev.entity_type === "Document"
                              ? "bg-purple-50 text-purple-700 border border-purple-200"
                              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          }`}
                        >
                          {ev.entity_type}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px]">
                        {isApp ? (
                          <button
                            onClick={() => onSelectApplication(ev.entity_id)}
                            className="text-primary-orange hover:underline font-medium"
                          >
                            {ev.details?.application_identifier || ev.entity_id.substring(0, 12)}...
                          </button>
                        ) : (
                          <span className="text-primary-text">{ev.entity_id.substring(0, 12)}...</span>
                        )}
                      </td>

                      <td className="py-3 px-4 font-semibold text-primary-text text-[11px]">
                        {formatActionName(ev.action)}
                      </td>

                      <td className="py-3 px-4 text-secondary-text text-[11px] max-w-md truncate" title={JSON.stringify(ev.details)}>
                        {ev.details ? (
                          <span>
                            {ev.details.comments ||
                              ev.details.action ||
                              (ev.details.previous_status && `${ev.details.previous_status} -> ${ev.details.new_status}`) ||
                              JSON.stringify(ev.details).substring(0, 70)}
                          </span>
                        ) : (
                          "Standard transaction recorded"
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedEvent(ev)}
                          className="p-1 text-secondary-text hover:text-primary-orange transition-colors"
                          title="View JSON Payload"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && events.length > 0 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-xs text-secondary-text">
            <span>
              Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, total)} of {total} audit records
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

      {/* JSON Payload Inspection Drawer */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg border border-border shadow-lg max-w-lg w-full p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h3 className="font-bold text-sm text-primary-text">Audit Event Payload Inspection</h3>
                <div className="text-[11px] text-secondary-text font-mono mt-0.5">ID: {selectedEvent.id}</div>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 text-secondary-text hover:text-primary-text rounded"
              >
                ✕
              </button>
            </div>

            <div className="text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-secondary-text">Action:</span>
                <span className="font-semibold">{selectedEvent.action}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-text">Entity:</span>
                <span className="font-mono">{selectedEvent.entity_type} ({selectedEvent.entity_id})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-text">Recorded At:</span>
                <span className="font-mono">{formatDateTime(selectedEvent.created_at)}</span>
              </div>
            </div>

            <div>
              <div className="text-[11px] font-semibold text-secondary-text mb-1">Raw Payload Details:</div>
              <pre className="p-3 bg-surface rounded text-[11px] font-mono text-primary-text overflow-x-auto max-h-60 border border-border/60">
                {JSON.stringify(selectedEvent.details, null, 2)}
              </pre>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-3.5 py-1.5 bg-primary-orange text-white text-xs font-medium rounded-md hover:bg-primary-orange-hover"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
