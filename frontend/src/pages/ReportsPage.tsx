import React, { useState, useEffect } from "react";
import {
  FileBarChart2,
  Download,
  RotateCw,
  PieChart,
  BarChart2,
  ShieldAlert,
  Building2,
  FileCheck2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  MapPin,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";
import { AnalyticsReport } from "../types";
import { formatDate } from "../lib/utils";

interface ReportsPageProps {
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({
  onSelectApplication,
  refreshTrigger,
}) => {
  const [data, setData] = useState<AnalyticsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [refreshTrigger]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAnalyticsReport();
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load regulatory analytics");
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      // Fetch up to 100 applications to export authentic dataset
      const res = await api.getApplications({ page: 1, limit: 100 });
      const headers = ["Application Code", "Institution", "Category", "Academic Year", "Status", "Submission Date"];
      const rows = res.items.map((app) => [
        `"${app.application_identifier}"`,
        `"${app.institution_name.replace(/"/g, '""')}"`,
        `"${app.application_category}"`,
        `"${app.academic_year}"`,
        `"${app.status}"`,
        `"${app.submission_date}"`,
      ]);

      const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `AICTE_Regulatory_Dossier_Export_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
        <RotateCw className="w-6 h-6 animate-spin text-primary-orange" />
        <span>Aggregating regulatory compliance reports and risk metrics...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex flex-col items-center space-y-2">
          <AlertCircle className="w-6 h-6 text-red-500" />
          <span className="font-semibold">{error || "Failed to generate report"}</span>
          <button
            onClick={fetchAnalytics}
            className="px-3 py-1 bg-white border border-red-300 rounded text-red-800 hover:bg-red-100"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-primary-text tracking-tight">Regulatory Reports & Analytics</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
              APH 2026-27 Active
            </span>
          </div>
          <p className="text-xs text-secondary-text mt-0.5">
            Aggregated institutional compliance metrics, deterministic risk profiles, and council audit exports
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchAnalytics}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
          >
            <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
            <span>Refresh Data</span>
          </button>

          <button
            disabled={exporting}
            onClick={handleExportCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-primary-orange text-white text-xs font-medium rounded-md hover:bg-primary-orange-hover transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exporting ? "Generating..." : "Export CSV Dossier"}</span>
          </button>
        </div>
      </div>

      {/* Aggregate KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Total Applications</span>
            <Layers className="w-4 h-4 text-primary-orange" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">{data.total_applications}</div>
          <div className="text-[11px] text-secondary-text mt-1">Across 4 statutory categories</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Institutions Registry</span>
            <Building2 className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">{data.total_institutions}</div>
          <div className="text-[11px] text-secondary-text mt-1">Normalized location uniqueness active</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Uploaded Documents</span>
            <FileCheck2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">{data.total_documents}</div>
          <div className="text-[11px] text-secondary-text mt-1">Private persistent BLOB storage</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Compliance Findings</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">{data.total_findings}</div>
          <div className="text-[11px] text-secondary-text mt-1">Flagged statutory deficiencies</div>
        </div>
      </div>

      {/* Analytics Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application Status Breakdown */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-primary-text flex items-center space-x-2">
              <PieChart className="w-4 h-4 text-primary-orange" />
              <span>Application Status Breakdown</span>
            </h3>
          </div>

          <div className="space-y-3">
            {Object.entries(data.status_breakdown).map(([status, count]) => {
              const pct = data.total_applications > 0 ? Math.round((count / data.total_applications) * 100) : 0;
              return (
                <div key={status} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-primary-text">{status}</span>
                    <span className="text-secondary-text font-mono">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-surface-muted rounded-full h-2 overflow-hidden border border-border/40">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        status === "Verified" || status === "Approved"
                          ? "bg-emerald-500"
                          : status === "Action Required"
                          ? "bg-amber-500"
                          : "bg-blue-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Deterministic Risk Distribution */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-primary-text flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span>Risk Tier Distribution</span>
            </h3>
            <span className="text-[10px] text-secondary-text">Weights: APH Clause 2.4</span>
          </div>

          <div className="space-y-3">
            {Object.entries(data.risk_breakdown).map(([band, count]) => {
              const totalEvaluated = Object.values(data.risk_breakdown).reduce((a, b) => a + b, 0);
              const pct = totalEvaluated > 0 ? Math.round((count / totalEvaluated) * 100) : 0;
              return (
                <div key={band} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-primary-text">{band} Risk</span>
                    <span className="text-secondary-text font-mono">{count} applications ({pct}%)</span>
                  </div>
                  <div className="w-full bg-surface-muted rounded-full h-2 overflow-hidden border border-border/40">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        band === "High" || band === "Extreme"
                          ? "bg-red-500"
                          : band === "Medium"
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Categories Distribution */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-primary-text flex items-center space-x-2">
              <BarChart2 className="w-4 h-4 text-blue-600" />
              <span>Application Categories</span>
            </h3>
          </div>

          <div className="space-y-2.5 text-xs">
            {Object.entries(data.category_breakdown).map(([cat, count]) => (
              <div key={cat} className="flex items-center justify-between py-1.5 border-b border-border/40 last:border-0">
                <span className="font-medium text-primary-text">{cat}</span>
                <span className="px-2 py-0.5 rounded bg-surface text-secondary-text font-mono text-[11px] border border-border/60">
                  {count} applications
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* State-wise Distribution */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-primary-text flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-emerald-600" />
              <span>Top Regional Volumes</span>
            </h3>
          </div>

          <div className="space-y-2.5 text-xs">
            {Object.entries(data.state_distribution).map(([state, count]) => (
              <div key={state} className="flex items-center justify-between py-1.5 border-b border-border/40 last:border-0">
                <span className="font-medium text-primary-text">{state}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-mono text-[11px] border border-emerald-200">
                  {count} applications
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
