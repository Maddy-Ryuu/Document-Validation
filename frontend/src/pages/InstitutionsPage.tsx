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
                  <th className="py-2.5 px-4 text-right">Linked Applications</th>
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
                    <td className="py-3 px-4 text-right font-mono font-semibold text-primary-text">
                      {inst.application_count ?? 0}
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
    </div>
  );
};
