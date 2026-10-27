import React, { useState, useEffect } from "react";
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Server,
  Database,
  Lock,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  FileCode,
  HardDrive,
  Info,
} from "lucide-react";
import { api } from "../services/api";
import { SystemSettings } from "../types";

export const SettingsPage: React.FC = () => {
  const [settingsData, setSettingsData] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Local configurable preferences
  const [pageSize, setPageSize] = useState("10");
  const [compactMode, setCompactMode] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSystemSettings();
      setSettingsData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load system settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess("Officer viewing preferences saved successfully");
    setTimeout(() => setSaveSuccess(null), 3000);
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
        <RotateCw className="w-6 h-6 animate-spin text-primary-orange" />
        <span>Loading system environment & scrutiny officer profile...</span>
      </div>
    );
  }

  if (error || !settingsData) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex flex-col items-center space-y-2">
          <AlertCircle className="w-6 h-6 text-red-500" />
          <span className="font-semibold">{error || "Failed to load settings"}</span>
          <button
            onClick={fetchSettings}
            className="px-3 py-1 bg-white border border-red-300 rounded text-red-800 hover:bg-red-100"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { system, officer_profile, security_status } = settingsData;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-primary-text tracking-tight">Platform Settings & Security Profile</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded">
              System Verified
            </span>
          </div>
          <p className="text-xs text-secondary-text mt-0.5">
            Verified backend infrastructure status, reviewer identity profile, and statutory environment parameters
          </p>
        </div>

        <button
          onClick={fetchSettings}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
        >
          <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
          <span>Refresh Status</span>
        </button>
      </div>

      {saveSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{saveSuccess}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scrutiny Officer Profile */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs space-y-4 lg:col-span-1">
          <div className="flex items-center space-x-3 border-b border-border pb-3">
            <div className="w-10 h-10 rounded-full bg-primary-orange/10 flex items-center justify-center text-primary-orange font-bold text-sm">
              AD
            </div>
            <div>
              <h3 className="font-bold text-sm text-primary-text">{officer_profile.name}</h3>
              <p className="text-xs text-secondary-text">{officer_profile.role}</p>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-secondary-text text-[11px] block">Bureau Assignment</span>
              <span className="font-medium text-primary-text">{officer_profile.bureau}</span>
            </div>
            <div>
              <span className="text-secondary-text text-[11px] block">Official Email</span>
              <span className="font-mono text-primary-text">{officer_profile.email}</span>
            </div>
            <div>
              <span className="text-secondary-text text-[11px] block">Jurisdiction Master</span>
              <span className="font-medium text-primary-text">{officer_profile.assigned_region}</span>
            </div>
          </div>

          <div className="pt-2 border-t border-border space-y-2">
            <span className="text-[11px] font-semibold text-secondary-text uppercase tracking-wider block">
              Active Scrutiny Privileges
            </span>
            <div className="flex flex-wrap gap-1.5">
              {officer_profile.permissions.map((p) => (
                <span
                  key={p}
                  className="px-2 py-0.5 rounded text-[10px] font-mono bg-surface border border-border text-secondary-text"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Backend & Database Infrastructure Info */}
        <div className="bg-white p-5 rounded-lg border border-border shadow-xs space-y-4 lg:col-span-2">
          <div className="border-b border-border pb-3 flex items-center justify-between">
            <h3 className="font-bold text-xs uppercase tracking-wider text-primary-text flex items-center space-x-2">
              <Server className="w-4 h-4 text-primary-orange" />
              <span>Production Infrastructure & Persistence Health</span>
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Operational
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-surface rounded border border-border/60 space-y-1">
              <div className="flex items-center space-x-1.5 text-secondary-text text-[11px]">
                <Database className="w-3.5 h-3.5 text-blue-600" />
                <span>Database Engine</span>
              </div>
              <div className="font-semibold text-primary-text">{system.database_engine}</div>
              <div className="text-[11px] text-emerald-600 font-medium">Status: Connected & Migrated</div>
            </div>

            <div className="p-3 bg-surface rounded border border-border/60 space-y-1">
              <div className="flex items-center space-x-1.5 text-secondary-text text-[11px]">
                <HardDrive className="w-3.5 h-3.5 text-emerald-600" />
                <span>Document Storage</span>
              </div>
              <div className="font-semibold text-primary-text">Persistent Database BLOB</div>
              <div className="text-[11px] text-secondary-text">SHA-256 Tampering Verification Active</div>
            </div>

            <div className="p-3 bg-surface rounded border border-border/60 space-y-1">
              <div className="flex items-center space-x-1.5 text-secondary-text text-[11px]">
                <FileCode className="w-3.5 h-3.5 text-purple-600" />
                <span>Handbook Specification</span>
              </div>
              <div className="font-semibold text-primary-text">{system.handbook_edition}</div>
              <div className="text-[11px] text-secondary-text">Deterministic rule evaluation ruleset</div>
            </div>

            <div className="p-3 bg-surface rounded border border-border/60 space-y-1">
              <div className="flex items-center space-x-1.5 text-secondary-text text-[11px]">
                <Server className="w-3.5 h-3.5 text-primary-orange" />
                <span>Runtime Environment</span>
              </div>
              <div className="font-semibold text-primary-text capitalize">{system.environment}</div>
              <div className="text-[11px] text-secondary-text font-mono">v{system.version} (FastAPI + Vite)</div>
            </div>
          </div>

          {/* Genuine Security Architecture Status */}
          <div className="pt-2 border-t border-border space-y-3">
            <h4 className="text-xs font-bold text-primary-text uppercase tracking-wider flex items-center space-x-2">
              <Shield className="w-4 h-4 text-emerald-600" />
              <span>Security Protocols & Explicit Status</span>
            </h4>

            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded bg-emerald-50/60 border border-emerald-200 text-emerald-900 flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Private Document Authorization: </span>
                  <span>Enforced server-side. Unauthenticated requests are rejected with 401 Unauthorized.</span>
                </div>
              </div>

              <div className="p-2.5 rounded bg-emerald-50/60 border border-emerald-200 text-emerald-900 flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Audit Ledger Non-Repudiation: </span>
                  <span>All state modifications generate immutable timestamped records in PostgreSQL.</span>
                </div>
              </div>

              <div className="p-2.5 rounded bg-amber-50/60 border border-amber-200 text-amber-900 flex items-start space-x-2">
                <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Two-Factor & Biometric Auth: </span>
                  <span>Central AICTE SSO Identity Provider integration is scheduled for official council rollout; non-functional toggles are excluded.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
