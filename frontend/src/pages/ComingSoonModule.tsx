import React from "react";
import { Clock, Shield, Sparkles } from "lucide-react";

interface ComingSoonModuleProps {
  title: string;
  description: string;
  phase?: string;
  highlights: string[];
}

export const ComingSoonModule: React.FC<ComingSoonModuleProps> = ({
  title,
  description,
  phase = "Phase 2 & 3",
  highlights,
}) => {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="border-b border-border pb-3">
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl font-bold text-primary-text tracking-tight">{title}</h2>
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-surface border border-border text-primary-orange font-semibold">
            {phase} Planned
          </span>
        </div>
        <p className="text-xs text-secondary-text mt-1">{description}</p>
      </div>

      <div className="bg-white rounded-lg border border-border p-8 shadow-xs space-y-6">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-surface rounded-lg border border-border text-primary-orange shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-primary-text">
              Architecture & Database Schema Ready
            </h3>
            <p className="text-xs text-secondary-text mt-1 leading-relaxed">
              The foundational database tables, relations, and backend models (such as{" "}
              <code className="text-primary-text font-mono bg-surface px-1 py-0.5 rounded">
                ValidationRule
              </code>
              ,{" "}
              <code className="text-primary-text font-mono bg-surface px-1 py-0.5 rounded">
                VerificationCheck
              </code>
              , and{" "}
              <code className="text-primary-text font-mono bg-surface px-1 py-0.5 rounded">
                AuditEvent
              </code>
              ) are already defined and provisioned in the database schema.
            </p>
          </div>
        </div>

        <div className="border-t border-border pt-6">
          <h4 className="text-xs font-semibold text-primary-text uppercase tracking-wider mb-3">
            Module Implementation Scope:
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {highlights.map((h, i) => (
              <div
                key={i}
                className="flex items-center space-x-2.5 p-3 rounded bg-surface/60 border border-border text-xs text-primary-text"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-primary-orange shrink-0" />
                <span>{h}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
