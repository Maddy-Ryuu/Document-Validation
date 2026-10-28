import React, { useState } from "react";
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2 } from "lucide-react";
import { api } from "../services/api";
import { AuthUser } from "../types";

interface LoginPageProps {
  onLoginSuccess: (user: AuthUser) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError("Please provide both official email and password.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.login({ email: email.trim(), password });
      onLoginSuccess(res.user);
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please verify your official AICTE login.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (quickEmail: string, quickPass: string) => {
    setEmail(quickEmail);
    setPassword(quickPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-surface-muted/40 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand / Emblem Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 bg-primary-orange rounded-xl mx-auto flex items-center justify-center text-white shadow-md">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-primary-text tracking-tight">
              AICTE Application Validation Portal
            </h1>
            <p className="text-xs text-secondary-text mt-0.5">
              Approval Process Handbook (APH 2026-27) Statutory Scrutiny Bureau
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl border border-border shadow-sm p-6 sm:p-8 space-y-6">
          <div className="space-y-1">
            <h2 className="text-sm font-bold text-primary-text uppercase tracking-wider">
              Official Officer Sign In
            </h2>
            <p className="text-xs text-secondary-text">
              Enter your authorized credentials to access regulatory review queues and verification dossiers.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-primary-text mb-1">
                Official Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="e.g. officer@aicte.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-border rounded-lg text-primary-text placeholder:text-secondary-text/50 focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-primary-text mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="Enter your security password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-border rounded-lg text-primary-text placeholder:text-secondary-text/50 focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-primary-orange hover:bg-primary-orange-hover text-white text-xs font-semibold rounded-lg shadow-xs transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? "Authenticating..." : "Sign In to Portal"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick-Select Bootstrap Demonstration Credentials */}
          <div className="pt-4 border-t border-border space-y-2.5">
            <span className="text-[11px] font-semibold text-secondary-text block">
              Designated Scrutiny Accounts:
            </span>
            <div className="space-y-1.5 text-[11px]">
              <button
                type="button"
                onClick={() => handleQuickLogin("officer@aicte.gov.in", "aicte2026!")}
                className="w-full p-2 bg-surface-muted/60 hover:bg-surface border border-border rounded flex items-center justify-between text-left transition-colors"
              >
                <div>
                  <span className="font-semibold text-primary-text block">AICTE Scrutiny Officer</span>
                  <span className="text-secondary-text text-[10px]">officer@aicte.gov.in</span>
                </div>
                <span className="text-[10px] text-primary-orange font-medium">Use &rarr;</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("reviewer@aicte.gov.in", "reviewer2026!")}
                className="w-full p-2 bg-surface-muted/60 hover:bg-surface border border-border rounded flex items-center justify-between text-left transition-colors"
              >
                <div>
                  <span className="font-semibold text-primary-text block">Senior Reviewer</span>
                  <span className="text-secondary-text text-[10px]">reviewer@aicte.gov.in</span>
                </div>
                <span className="text-[10px] text-primary-orange font-medium">Use &rarr;</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("admin@aicte.gov.in", "admin2026!")}
                className="w-full p-2 bg-surface-muted/60 hover:bg-surface border border-border rounded flex items-center justify-between text-left transition-colors"
              >
                <div>
                  <span className="font-semibold text-primary-text block">System Administrator</span>
                  <span className="text-secondary-text text-[10px]">admin@aicte.gov.in</span>
                </div>
                <span className="text-[10px] text-primary-orange font-medium">Use &rarr;</span>
              </button>
            </div>
          </div>
        </div>

        {/* Security Notice */}
        <div className="text-center text-[11px] text-secondary-text flex items-center justify-center space-x-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Secured with cryptographic HMAC-SHA256 session auditing</span>
        </div>
      </div>
    </div>
  );
};
