import React, { useState, useEffect } from "react";
import { X, Building2, Plus, AlertCircle } from "lucide-react";
import { api } from "../services/api";
import { Institution } from "../types";

interface NewApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newApp: any) => void;
}

export const NewApplicationModal: React.FC<NewApplicationModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstId, setSelectedInstId] = useState("");
  const [category, setCategory] = useState("Extension of Approval (EoA)");
  const [academicYear, setAcademicYear] = useState("2026-2027");
  const [customAppId, setCustomAppId] = useState("");
  const [loadingInst, setLoadingInst] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadInstitutions();
      setError(null);
    }
  }, [isOpen]);

  const loadInstitutions = async () => {
    setLoadingInst(true);
    try {
      const res = await api.getInstitutions({ limit: 100 });
      setInstitutions(res.items);
      if (res.items.length > 0 && !selectedInstId) {
        setSelectedInstId(res.items[0].id);
      }
    } catch (err: any) {
      setError("Failed to load institutions list");
    } finally {
      setLoadingInst(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstId) {
      setError("Please select an institution");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const created = await api.createApplication({
        institution_id: selectedInstId,
        application_category: category,
        academic_year: academicYear,
        application_identifier: customAppId.trim() || undefined,
      });

      onSuccess(created);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to create application");
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-lg border border-border shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-surface">
          <div>
            <h2 className="text-sm font-bold text-primary-text">Create New Application</h2>
            <p className="text-[11px] text-secondary-text">AICTE Approval Process Handbook (APH 2026-27)</p>
          </div>
          <button
            onClick={onClose}
            className="text-secondary-text hover:text-primary-text p-1 rounded hover:bg-surface-muted transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-status-error flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Institution Selector */}
          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Select Institution <span className="text-status-error">*</span>
            </label>
            {loadingInst ? (
              <div className="h-9 bg-surface animate-pulse rounded border border-border" />
            ) : institutions.length === 0 ? (
              <div className="text-xs text-secondary-text p-2 bg-surface rounded border border-border">
                No institutions registered yet. Please create an institution first.
              </div>
            ) : (
              <select
                value={selectedInstId}
                onChange={(e) => setSelectedInstId(e.target.value)}
                required
                className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
              >
                {institutions.map((inst) => (
                  <option key={inst.id} value={inst.id}>
                    {inst.name} ({inst.institution_identifier} - {inst.city})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Application Category <span className="text-status-error">*</span>
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
            >
              <option value="Extension of Approval (EoA)">Extension of Approval (EoA)</option>
              <option value="Increase in Intake">Increase in Intake</option>
              <option value="New Institute">New Technical Institute</option>
              <option value="NRI / Foreign National Quota">NRI / Foreign National Quota</option>
              <option value="Change of Site / Location">Change of Site / Location</option>
            </select>
          </div>

          {/* Academic Year */}
          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Academic Year <span className="text-status-error">*</span>
            </label>
            <select
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
            >
              <option value="2026-2027">2026-2027 (Current Cycle)</option>
              <option value="2027-2028">2027-2028</option>
            </select>
          </div>

          {/* Custom App ID (Optional) */}
          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Custom Application ID <span className="text-secondary-text font-normal">(Optional)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. AICTE-2026-99214 (leave blank to auto-generate)"
              value={customAppId}
              onChange={(e) => setCustomAppId(e.target.value)}
              className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
            />
          </div>

          <div className="pt-2 flex items-center justify-end space-x-2 border-t border-border mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium text-secondary-text hover:text-primary-text hover:bg-surface rounded border border-border transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || institutions.length === 0}
              className="px-4 py-2 text-xs font-medium text-white bg-primary-orange hover:bg-primary-orange-hover rounded transition-colors shadow-xs disabled:opacity-50 flex items-center gap-1.5"
            >
              {submitting ? "Submitting..." : "Create Application"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
