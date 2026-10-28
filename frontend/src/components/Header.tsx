import React from "react";
import { Bell, LogOut } from "lucide-react";
import { AuthUser } from "../types";

interface HeaderProps {
  title: string;
  subtitle?: string;
  rightAction?: React.ReactNode;
  user?: AuthUser | null;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, rightAction, user, onLogout }) => {
  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase()
    : "AO";

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
        <div className="flex items-center space-x-3 pl-2 border-l border-border">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-primary-orange/10 border border-primary-orange/20 flex items-center justify-center text-xs font-bold text-primary-orange">
              {initials}
            </div>
            <div className="hidden sm:flex flex-col">
              <span className="text-xs font-semibold text-primary-text leading-tight">
                {user?.name || "AICTE Officer"}
              </span>
              <span className="text-[10px] text-secondary-text font-normal leading-tight capitalize">
                {user?.role?.replace(/_/g, " ") || "Approval Bureau"}
              </span>
            </div>
          </div>

          {onLogout && (
            <button
              onClick={onLogout}
              title="Sign Out of Portal"
              className="flex items-center space-x-1 px-2.5 py-1 text-xs text-secondary-text hover:text-red-700 hover:bg-red-50 border border-border rounded transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Log Out</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
