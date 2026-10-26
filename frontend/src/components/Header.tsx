import React from "react";
import { Bell, Search, UserCircle, CheckCircle, AlertTriangle, ShieldCheck } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  rightAction?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, rightAction }) => {
  return (
    <header className="h-16 border-b border-border bg-white px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-lg font-bold text-primary-text tracking-tight flex items-center gap-2">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-secondary-text font-normal">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center space-x-4">
        {rightAction}

        <div className="h-5 w-[1px] bg-border mx-1" />

        {/* Notifications */}
        <button
          title="Notifications"
          className="relative p-2 text-secondary-text hover:text-primary-text hover:bg-surface rounded-md transition-colors"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary-orange rounded-full" />
        </button>

        {/* User Profile */}
        <div className="flex items-center space-x-2 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-surface-muted border border-border flex items-center justify-center text-xs font-semibold text-primary-text">
            AD
          </div>
          <div className="hidden sm:flex flex-col">
            <span className="text-xs font-medium text-primary-text leading-tight">
              AICTE Officer
            </span>
            <span className="text-[10px] text-secondary-text font-normal leading-tight">
              Approval Bureau
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
