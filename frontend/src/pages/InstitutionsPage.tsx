import React, { useState, useEffect } from "react";
import {
  Building2,
  Search,
  Plus,
  MapPin,
  GraduationCap,
  Layers,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  Trash2,
  AlertTriangle,
  X,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";
import { api } from "../services/api";
import { Institution } from "../types";
import { formatDate } from "../lib/utils";

interface InstitutionsPageProps {
  onOpenNewInstModal: () => void;
  refreshTrigger: number;
}

export const InstitutionsPage: React.FC<InstitutionsPageProps> = ({
  onOpenNewInstModal,
  refreshTrigger,
}) => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Institution deletion modal state
  const [instToDelete, setInstToDelete] = useState<Institution | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  useEffect(() => {
    fetchInstitutions();
  }, [page, refreshTrigger]);

  const fetchInstitutions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getInstitutions({
        page,
        limit: 10,
        search: search.trim() || undefined,
      });
      setInstitutions(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      setError(err.message || "Failed to load institutions");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchInstitutions();
  };

  const confirmDelete = async () => {
    if (!instToDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteInstitution(instToDelete.id);
      setActionFeedback(
        `Institution "${instToDelete.name}" (${instToDelete.institution_identifier}) deleted successfully. Forensic audit record preserved.`
      );
      setInstToDelete(null);
      fetchInstitutions();
    } catch (err: any) {
      setDeleteError(err.message || "Failed to delete institution");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h2 className="text-2xl font-bold text-primary-text tracking-tight">Institutions Master Registry</h2>
          <p className="text-xs text-secondary-text mt-0.5">
            Registered technical institutes, colleges, and polytechnics under AICTE purview
          </p>
        </div>

        <button
          onClick={onOpenNewInstModal}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-primary-orange hover:bg-primary-orange-hover text-white text-xs font-medium rounded-md shadow-xs transition-colors self-start md:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Institution</span>
        </button>
      </div>

      {/* Success / Action Feedback Banner */}
      {actionFeedback && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-md text-xs text-emerald-800 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{actionFeedback}</span>
          </div>
          <button
            onClick={() => setActionFeedback(null)}
            className="text-emerald-600 hover:text-emerald-900 ml-3"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search & Actions Bar */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by code, institute name, state, or city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          />
        </form>

        <button
          onClick={fetchInstitutions}
          title="Refresh"
          className="p-1.5 bg-white border border-border rounded-md text-secondary-text hover:text-primary-text hover:bg-surface transition-colors"
        >
          <RotateCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Grid or Table */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-10 bg-surface animate-pulse rounded" />
            ))}
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-status-error">
            <p>{error}</p>
            <button
              onClick={fetchInstitutions}
              className="mt-2 px-3 py-1 bg-surface text-primary-text border border-border rounded text-xs"
            >
              Retry
            </button>
          </div>
        ) : institutions.length === 0 ? (
          <div className="p-12 text-center">
            <Building2 className="w-8 h-8 text-secondary-text/40 mx-auto mb-2" />
            <p className="text-xs font-semibold text-primary-text">No institutions found</p>
            <p className="text-[11px] text-secondary-text mt-0.5">
              Click &quot;New Institution&quot; to register an approved technical college.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface text-[11px] font-semibold text-secondary-text">
                  <th className="py-2.5 px-4">AICTE Code</th>
                  <th className="py-2.5 px-4">Institution Name</th>
                  <th className="py-2.5 px-4">Discipline Type</th>
                  <th className="py-2.5 px-4">State & City</th>
                  <th className="py-2.5 px-4">Registered Date</th>
                  <th className="py-2.5 px-4 text-center">Linked Applications</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {institutions.map((inst) => (
                  <tr key={inst.id} className="hover:bg-surface/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-primary-orange">
                      {inst.institution_identifier}
                    </td>
                    <td className="py-3 px-4 font-medium text-primary-text">{inst.name}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface border border-border text-[11px] text-secondary-text">
                        {inst.institution_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-secondary-text">
                      {inst.city}, {inst.state}
                    </td>
                    <td className="py-3 px-4 text-secondary-text">{formatDate(inst.created_at)}</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-primary-text">
                      {inst.application_count ?? 0}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          setDeleteError(null);
                          setInstToDelete(inst);
                        }}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 text-[11px] font-medium text-red-600 hover:text-red-700 hover:bg-red-50 border border-red-200 rounded transition-colors"
                        title={`Delete ${inst.name}`}
                      >
                        <Trash2 className="w-3 h-3" />
                        <span>Delete</span>
                      </button>
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
              Page {page} of {pages} ({total} institutions)
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

      {/* Confirmation Modal for Institution Deletion */}
      {instToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg border border-border shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-4 border-b border-border flex items-center justify-between bg-surface/40">
              <div className="flex items-center space-x-2 text-red-600">
                <Trash2 className="w-4 h-4" />
                <h3 className="font-semibold text-sm text-primary-text">Confirm Institution Deletion</h3>
              </div>
              <button
                onClick={() => setInstToDelete(null)}
                disabled={deleting}
                className="text-secondary-text hover:text-primary-text"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              {deleteError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                  <div className="leading-relaxed font-medium">{deleteError}</div>
                </div>
              )}

              <p className="text-secondary-text leading-relaxed">
                Are you sure you want to delete institution <strong className="text-primary-text">{instToDelete.name}</strong> (<span className="font-mono text-primary-orange">{instToDelete.institution_identifier}</span>)?
              </p>

              {/* Institution Summary Box */}
              <div className="p-3 bg-surface rounded border border-border space-y-1.5 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-secondary-text">Discipline:</span>
                  <span className="font-medium text-primary-text">{instToDelete.institution_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary-text">Location:</span>
                  <span className="font-medium text-primary-text">{instToDelete.city}, {instToDelete.state}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary-text">Linked Applications:</span>
                  <span className="font-semibold font-mono text-primary-text">{instToDelete.application_count ?? 0}</span>
                </div>
              </div>

              {/* Warning if linked applications exist */}
              {(instToDelete.application_count ?? 0) > 0 && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-800 space-y-1">
                  <div className="flex items-center space-x-1.5 font-semibold text-amber-900">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    <span>Active Regulatory History Detected</span>
                  </div>
                  <p className="leading-relaxed">
                    This institution has <strong className="text-amber-950 font-bold">{instToDelete.application_count}</strong> active application(s).
                    The AICTE regulatory engine strictly prohibits deleting institutions with active applications to prevent orphaned records. Linked applications must be resolved or deleted first.
                  </p>
                </div>
              )}

              {/* Statutory Audit and Reference Data Notice */}
              <div className="p-3 bg-surface-muted rounded border border-border text-[11px] text-secondary-text space-y-1">
                <div className="flex items-center space-x-1.5 font-semibold text-primary-text">
                  <ShieldAlert className="w-3.5 h-3.5 text-primary-orange" />
                  <span>Statutory Audit & Reference Protection:</span>
                </div>
                <p className="leading-relaxed">
                  Only authorized Administrators may delete institutions. An immutable forensic audit record will be logged with full deletion metadata. Central regulatory reference benchmarks and synthetic control datasets are strictly protected and cannot be deleted through this interface.
                </p>
              </div>
            </div>

            <div className="p-3 bg-surface-muted/60 border-t border-border flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setInstToDelete(null)}
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
