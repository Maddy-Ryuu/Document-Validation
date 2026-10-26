import React, { useState, useEffect } from "react";
import {
  FileText,
  Clock,
  AlertCircle,
  CheckCircle2,
  Calendar,
  Filter,
  Plus,
  Search,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  RotateCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { api } from "../services/api";
import { DashboardSummary, TrendPoint, ApplicationListItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../lib/utils";

interface OverviewProps {
  onOpenNewAppModal: () => void;
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const Overview: React.FC<OverviewProps> = ({
  onOpenNewAppModal,
  onSelectApplication,
  refreshTrigger,
}) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [totalApps, setTotalApps] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  // Loading & Error states
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingApps, setLoadingApps] = useState(true);
  const [errorSummary, setErrorSummary] = useState<string | null>(null);
  const [errorApps, setErrorApps] = useState<string | null>(null);

  useEffect(() => {
    fetchSummaryAndTrends();
  }, [refreshTrigger]);

  useEffect(() => {
    fetchApplications();
  }, [page, statusFilter, refreshTrigger]);

  const fetchSummaryAndTrends = async () => {
    setLoadingSummary(true);
    setErrorSummary(null);
    try {
      const [sumRes, trendRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getDashboardTrends(14),
      ]);
      setSummary(sumRes);
      setTrends(trendRes.trends);
    } catch (err: any) {
      setErrorSummary(err.message || "Failed to load dashboard metrics");
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchApplications = async () => {
    setLoadingApps(true);
    setErrorApps(null);
    try {
      const res = await api.getApplications({
        page,
        limit: 8,
        search: search.trim() || undefined,
        status: statusFilter,
      });
      setApplications(res.items);
      setTotalApps(res.total);
      setTotalPages(res.pages);
    } catch (err: any) {
      setErrorApps(err.message || "Failed to load applications");
    } finally {
      setLoadingApps(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchApplications();
  };

  // Pie chart data
  const pieData = summary
    ? [
        { name: "Verified", value: summary.status_breakdown["Verified"] || 0, color: "#287A52" },
        { name: "Under Validation", value: summary.status_breakdown["Under Validation"] || 0, color: "#F07836" },
        { name: "Action Required", value: summary.status_breakdown["Action Required"] || 0, color: "#C7463A" },
        { name: "Approved", value: summary.status_breakdown["Approved"] || 0, color: "#3B82F6" },
      ].filter((d) => d.value > 0)
    : [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Editorial Title Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h2 className="text-3xl font-bold font-editorial italic tracking-tight text-primary-text">
            Application Overview
          </h2>
          <p className="text-xs text-secondary-text mt-0.5 font-normal">
            Validation & Compliance Workspace • AICTE Regulatory Scrutiny
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-surface px-3 py-1.5 rounded-md border border-border text-xs text-secondary-text">
            <Calendar className="w-3.5 h-3.5 text-secondary-text" />
            <span>Academic Cycle 2026-27</span>
          </div>

          <button
            onClick={onOpenNewAppModal}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-primary-orange hover:bg-primary-orange-hover text-white text-xs font-medium rounded-md shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Application</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Applications */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs hover:border-border/80 transition-shadow">
          <div className="flex items-center justify-between text-secondary-text mb-2">
            <span className="text-xs font-medium">Total Applications</span>
            <div className="w-7 h-7 rounded bg-surface flex items-center justify-center text-primary-text">
              <FileText className="w-4 h-4 text-primary-orange" />
            </div>
          </div>
          {loadingSummary ? (
            <div className="h-8 bg-surface animate-pulse rounded w-16" />
          ) : (
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-primary-text">
                {summary?.total_applications ?? 0}
              </span>
              <span className="text-[11px] text-secondary-text">recorded</span>
            </div>
          )}
        </div>

        {/* Card 2: In Validation */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs hover:border-border/80 transition-shadow">
          <div className="flex items-center justify-between text-secondary-text mb-2">
            <span className="text-xs font-medium">In Validation</span>
            <div className="w-7 h-7 rounded bg-surface flex items-center justify-center text-primary-text">
              <Clock className="w-4 h-4 text-[#B96A19]" />
            </div>
          </div>
          {loadingSummary ? (
            <div className="h-8 bg-surface animate-pulse rounded w-16" />
          ) : (
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-primary-text">
                {summary?.in_validation ?? 0}
              </span>
              <span className="text-[11px] text-[#B96A19] font-medium">active scrutiny</span>
            </div>
          )}
        </div>

        {/* Card 3: Action Required */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs hover:border-border/80 transition-shadow">
          <div className="flex items-center justify-between text-secondary-text mb-2">
            <span className="text-xs font-medium">Action Required</span>
            <div className="w-7 h-7 rounded bg-surface flex items-center justify-center text-primary-text">
              <AlertCircle className="w-4 h-4 text-status-error" />
            </div>
          </div>
          {loadingSummary ? (
            <div className="h-8 bg-surface animate-pulse rounded w-16" />
          ) : (
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-primary-text">
                {summary?.action_required ?? 0}
              </span>
              <span className="text-[11px] text-status-error font-medium">discrepancies</span>
            </div>
          )}
        </div>

        {/* Card 4: Verified Documents */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs hover:border-border/80 transition-shadow">
          <div className="flex items-center justify-between text-secondary-text mb-2">
            <span className="text-xs font-medium">Risk Distribution</span>
            <div className="w-7 h-7 rounded bg-surface flex items-center justify-center text-primary-text">
              <CheckCircle2 className="w-4 h-4 text-primary-orange" />
            </div>
          </div>
          {loadingSummary ? (
            <div className="h-8 bg-surface animate-pulse rounded w-16" />
          ) : (
            <div className="flex items-center space-x-2 pt-1 text-xs font-mono">
              <span className="text-status-success font-bold">
                L: {summary?.risk_breakdown?.["Low"] ?? 0}
              </span>
              <span className="text-secondary-text">•</span>
              <span className="text-status-warning font-bold">
                M: {summary?.risk_breakdown?.["Medium"] ?? 0}
              </span>
              <span className="text-secondary-text">•</span>
              <span className="text-status-error font-bold">
                H: {summary?.risk_breakdown?.["High"] ?? 0}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Line Chart: Application Activity */}
        <div className="lg:col-span-2 bg-white p-5 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-primary-text">Application Activity</h3>
              <p className="text-[11px] text-secondary-text">Submission & verification trend over past 14 days</p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-primary-orange" />
                <span className="text-[11px] text-secondary-text">Submissions</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-status-success" />
                <span className="text-[11px] text-secondary-text">Verified</span>
              </div>
            </div>
          </div>

          <div className="h-56 w-full">
            {trends.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-secondary-text bg-surface/40 rounded border border-dashed border-border">
                No activity data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#73716C" }} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#73716C" }} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#E9E6E0",
                      borderRadius: "6px",
                      fontSize: "11px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="applications"
                    stroke="#F07836"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#F07836" }}
                    name="Submitted"
                  />
                  <Line
                    type="monotone"
                    dataKey="verified"
                    stroke="#287A52"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#287A52" }}
                    name="Verified"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Donut Chart: Validation Status */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-primary-text">Validation Status</h3>
            <p className="text-[11px] text-secondary-text">Distribution across all stages</p>
          </div>

          <div className="h-44 flex items-center justify-center my-2">
            {pieData.length === 0 ? (
              <div className="text-xs text-secondary-text">No records to chart</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#E9E6E0",
                      borderRadius: "6px",
                      fontSize: "11px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border text-[11px]">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-secondary-text truncate">{item.name}</span>
                <span className="font-semibold text-primary-text ml-auto">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Applications Section */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {/* Table Toolbar */}
        <div className="p-4 border-b border-border flex flex-col md:flex-row md:items-center justify-between gap-3 bg-surface/50">
          <div>
            <h3 className="text-sm font-semibold text-primary-text">Recent Applications</h3>
            <p className="text-[11px] text-secondary-text">
              Showing {applications.length} of {totalApps} total submissions
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {/* Search */}
            <form onSubmit={handleSearchSubmit} className="relative">
              <Search className="w-3.5 h-3.5 text-secondary-text absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search ID, college, city..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange w-48 sm:w-60"
              />
            </form>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
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

            <button
              onClick={() => {
                fetchApplications();
                fetchSummaryAndTrends();
              }}
              title="Refresh"
              className="p-1.5 bg-white border border-border rounded-md text-secondary-text hover:text-primary-text hover:bg-surface transition-colors"
            >
              <RotateCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Table Body */}
        {loadingApps ? (
          <div className="p-8 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-10 bg-surface animate-pulse rounded" />
            ))}
          </div>
        ) : errorApps ? (
          <div className="p-8 text-center text-xs text-status-error">
            <p>{errorApps}</p>
            <button
              onClick={fetchApplications}
              className="mt-2 px-3 py-1 bg-surface text-primary-text border border-border rounded text-xs"
            >
              Retry
            </button>
          </div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-8 h-8 text-secondary-text/40 mx-auto mb-2" />
            <p className="text-xs font-semibold text-primary-text">No applications found</p>
            <p className="text-[11px] text-secondary-text mt-0.5">
              Try adjusting your search criteria or create a new application
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
                    <td className="py-3 px-4">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectApplication(app.id);
                        }}
                        className="text-primary-orange hover:text-primary-orange-hover font-medium inline-flex items-center gap-1 text-[11px]"
                      >
                        Review
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-3 border-t border-border flex items-center justify-between text-xs bg-surface/30">
            <span className="text-secondary-text text-[11px]">
              Page {page} of {totalPages}
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
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
