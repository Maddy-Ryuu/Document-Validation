import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  BookOpen,
  ExternalLink,
  RotateCw,
  Search,
  Filter,
} from "lucide-react";
import { api } from "../services/api";
import { RegulatoryRule } from "../types";

export const ComplianceRulesPage: React.FC = () => {
  const [rules, setRules] = useState<RegulatoryRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getComplianceRules();
      setRules(data);
    } catch (err: any) {
      setError(err.message || "Failed to load regulatory rules catalog");
    } finally {
      setLoading(false);
    }
  };

  const filteredRules = rules.filter((r) => {
    const matchesFilter = filterType === "ALL" || r.rule_type === filterType;
    const matchesSearch =
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.rule_code.toLowerCase().includes(search.toLowerCase()) ||
      r.category.toLowerCase().includes(search.toLowerCase()) ||
      r.description.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h2 className="text-2xl font-bold text-primary-text tracking-tight flex items-center gap-2">
            <span>Regulatory Compliance Rules</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-primary-orange font-semibold">
              APH 2026-27 Active
            </span>
          </h2>
          <p className="text-xs text-secondary-text mt-0.5">
            Configurable, traceable regulatory rules with official Approval Process Handbook section citations
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={loadRules}
            title="Refresh Catalog"
            className="p-1.5 rounded border border-border bg-white text-secondary-text hover:text-primary-text"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[260px]">
          <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search rules by code, name, category, or citation..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
          />
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-secondary-text font-medium">Type:</span>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-xs bg-white border border-border rounded px-2.5 py-1.5 text-primary-text focus:outline-none focus:border-primary-orange"
          >
            <option value="ALL">All Categories</option>
            <option value="OFFICIAL_REGULATORY">Official Regulatory Rules</option>
            <option value="TECHNICAL_CHECK">Technical Integrity Checks</option>
            <option value="PENDING_CONFIRMATION">Pending Confirmation</option>
          </select>
        </div>
      </div>

      {/* Rule Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-40 bg-surface animate-pulse rounded-lg border border-border" />
          ))}
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-status-error bg-white rounded-lg border border-border">
          <p>{error}</p>
          <button onClick={loadRules} className="mt-2 px-3 py-1 bg-surface border border-border rounded">
            Retry
          </button>
        </div>
      ) : filteredRules.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-lg border border-border">
          <p className="text-xs font-semibold text-primary-text">No matching regulatory rules found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRules.map((r) => (
            <div
              key={r.rule_code}
              className="bg-white rounded-lg border border-border p-5 shadow-xs hover:border-border/80 transition-shadow space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 pb-2 border-b border-border">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-primary-orange">
                        {r.rule_code}
                      </span>
                      <span className="text-[10px] font-mono text-secondary-text">v{r.rule_version}</span>
                    </div>
                    <h3 className="text-sm font-bold text-primary-text mt-0.5">{r.name}</h3>
                  </div>

                  <span
                    className={`text-[10px] font-medium px-2 py-0.5 rounded uppercase font-mono ${
                      r.rule_type === "OFFICIAL_REGULATORY"
                        ? "bg-green-50 text-status-success border border-green-200"
                        : r.rule_type === "TECHNICAL_CHECK"
                        ? "bg-blue-50 text-blue-700 border border-blue-200"
                        : "bg-amber-50 text-status-warning border border-amber-200"
                    }`}
                  >
                    {r.rule_type.replace(/_/g, " ")}
                  </span>
                </div>

                <p className="text-xs text-secondary-text leading-relaxed mt-2.5">
                  {r.description}
                </p>
              </div>

              {/* Regulatory Citation Box */}
              <div className="bg-surface/50 rounded p-3 border border-border/80 text-[11px] space-y-1">
                <div className="flex items-center space-x-1.5 text-primary-text font-semibold">
                  <BookOpen className="w-3.5 h-3.5 text-primary-orange" />
                  <span>{r.regulatory_source.title}</span>
                </div>
                <div className="text-secondary-text">
                  <span className="font-medium text-primary-text">Section:</span> {r.regulatory_source.section}
                </div>
                {r.regulatory_source.page && (
                  <div className="text-secondary-text">
                    <span className="font-medium text-primary-text">Reference:</span> {r.regulatory_source.page}
                  </div>
                )}
                {r.regulatory_source.source_url && (
                  <a
                    href={r.regulatory_source.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary-orange hover:underline inline-flex items-center gap-1 text-[10px] pt-1"
                  >
                    View Official Handbook Portal <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
