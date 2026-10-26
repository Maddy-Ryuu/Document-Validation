import React from "react";
import {
  LayoutDashboard,
  FileText,
  Building2,
  FileCheck2,
  ShieldCheck,
  CheckCircle2,
  ListTodo,
  History,
  FileBarChart2,
  Settings,
  ChevronRight,
  Shield,
  ExternalLink,
} from "lucide-react";

export type NavItemKey =
  | "overview"
  | "applications"
  | "institutions"
  | "documents"
  | "rules"
  | "verification"
  | "queue"
  | "audit"
  | "reports"
  | "settings";

interface SidebarProps {
  currentTab: NavItemKey;
  onSelectTab: (tab: NavItemKey) => void;
  collapsed?: boolean;
}

interface NavItemConfig {
  key: NavItemKey;
  label: string;
  icon: React.ElementType;
  badge?: string;
  isPhase1?: boolean;
}

const navItems: NavItemConfig[] = [
  { key: "overview", label: "Overview", icon: LayoutDashboard, isPhase1: true },
  { key: "applications", label: "Applications", icon: FileText, isPhase1: true },
  { key: "institutions", label: "Institutions", icon: Building2, isPhase1: true },
  { key: "documents", label: "Document Review", icon: FileCheck2 },
  { key: "rules", label: "Compliance Rules", icon: ShieldCheck, isPhase1: true, badge: "APH 26-27" },
  { key: "verification", label: "Verification Center", icon: CheckCircle2 },
  { key: "queue", label: "Review Queue", icon: ListTodo },
  { key: "audit", label: "Audit Trail", icon: History },
  { key: "reports", label: "Reports", icon: FileBarChart2 },
  { key: "settings", label: "Settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  return (
    <aside className="w-64 border-r border-border bg-surface flex flex-col h-screen select-none shrink-0 sticky top-0">
      {/* Branding Header */}
      <div className="h-16 border-b border-border px-5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-primary-orange flex items-center justify-center text-white shadow-sm font-bold text-sm tracking-wide">
            A
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold uppercase tracking-wider text-primary-text leading-tight">
              AICTE
            </span>
            <span className="text-[11px] text-secondary-text font-normal leading-tight">
              Validation & Compliance
            </span>
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-secondary-text uppercase tracking-wider">
          Workspace
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.key;

          return (
            <button
              key={item.key}
              onClick={() => onSelectTab(item.key)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-all duration-150 ${
                isActive
                  ? "bg-white text-primary-orange font-semibold shadow-xs border border-border/80"
                  : "text-primary-text/80 hover:bg-white/60 hover:text-primary-text"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? "text-primary-orange" : "text-secondary-text"
                  }`}
                />
                <span>{item.label}</span>
              </div>

              {!item.isPhase1 && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-muted text-secondary-text border border-border/50 uppercase font-mono">
                  Phase 2
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer Info / Authority Tag */}
      <div className="p-3 border-t border-border bg-surface-muted/50">
        <div className="flex items-center space-x-2.5 px-2 py-2 rounded border border-border/60 bg-white">
          <Shield className="w-4 h-4 text-primary-orange shrink-0" />
          <div className="flex flex-col overflow-hidden">
            <span className="text-[11px] font-medium text-primary-text truncate">
              Regulatory Portal
            </span>
            <span className="text-[10px] text-secondary-text truncate">
              Handshake v1.0 • Phase 1
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
