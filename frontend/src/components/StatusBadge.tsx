import React from "react";
import { CheckCircle2, Clock, AlertTriangle, XCircle, ShieldCheck } from "lucide-react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  switch (status) {
    case "Verified":
    case "Approved":
    case "REFERENCE_VERIFIED":
    case "AUTO_VERIFIED":
    case "OFFICIAL_VERIFIED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#EBF7F0] text-[#287A52] border border-[#287A52]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#287A52]" />
          {status}
        </span>
      );

    case "Under Validation":
    case "Submitted":
    case "Running":
    case "MANUAL_SCRUTINY_REQUIRED":
    case "Needs Review":
    case "OUTDATED_APPROVAL":
    case "PROVISIONAL_PENDING":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#FFF8EB] text-[#B96A19] border border-[#B96A19]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#B96A19] animate-pulse" />
          {status}
        </span>
      );

    case "Action Required":
    case "Discrepancy":
    case "Clarification Requested":
    case "REFERENCE_MISMATCH":
    case "REFERENCE_NOT_FOUND":
    case "UNAPPROVED_QUOTA":
    case "ADVERSE_STANDING":
    case "REJECT_UNAUTHORIZED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#FDEDED] text-[#C7463A] border border-[#C7463A]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#C7463A]" />
          {status}
        </span>
      );

    case "SYNTHETIC_BENCHMARK":
    case "UNVERIFIED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-300">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
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
