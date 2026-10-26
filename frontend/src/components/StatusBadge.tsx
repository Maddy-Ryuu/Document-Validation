import React from "react";
import { CheckCircle2, Clock, AlertTriangle, XCircle, ShieldCheck } from "lucide-react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  switch (status) {
    case "Verified":
    case "Approved":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#EBF7F0] text-[#287A52] border border-[#287A52]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#287A52]" />
          {status}
        </span>
      );

    case "Under Validation":
    case "Submitted":
    case "Running":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#FFF8EB] text-[#B96A19] border border-[#B96A19]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#B96A19] animate-pulse" />
          {status}
        </span>
      );

    case "Action Required":
    case "Discrepancy":
    case "Clarification Requested":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#FDEDED] text-[#C7463A] border border-[#C7463A]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#C7463A]" />
          {status}
        </span>
      );

    case "Rejected":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-700 border border-gray-300">
          <span className="w-1.5 h-1.5 rounded-full bg-gray-500" />
          {status}
        </span>
      );

    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-surface-muted text-secondary-text border border-border">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary-text" />
          {status}
        </span>
      );
  }
};
