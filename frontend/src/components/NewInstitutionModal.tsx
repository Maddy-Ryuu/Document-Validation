import React, { useState } from "react";
import { X, Building2, AlertCircle } from "lucide-react";
import { api } from "../services/api";
import { Institution } from "../types";

interface NewInstitutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newInst: Institution) => void;
}

export const NewInstitutionModal: React.FC<NewInstitutionModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [identifier, setIdentifier] = useState("");
  const [name, setName] = useState("");
  const [institutionType, setInstitutionType] = useState("Engineering");
  const [state, setState] = useState("Delhi");
  const [city, setCity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !name.trim() || !city.trim()) {
      setError("Please fill in all required fields");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const created = await api.createInstitution({
        institution_identifier: identifier.trim().toUpperCase(),
        name: name.trim(),
        institution_type: institutionType,
        state,
        city: city.trim(),
      });
      onSuccess(created);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to create institution");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-lg border border-border shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-surface">
          <div>
            <h2 className="text-sm font-bold text-primary-text">Register New Institution</h2>
            <p className="text-[11px] text-secondary-text">AICTE Institutional Master Registry</p>
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

          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Institution AICTE Code / Identifier <span className="text-status-error">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. AICTE-INST-008"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Institution Name <span className="text-status-error">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. National Institute of Technology & Engineering"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange focus:ring-1 focus:ring-primary-orange"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-primary-text mb-1">
                Discipline Type <span className="text-status-error">*</span>
              </label>
              <select
                value={institutionType}
                onChange={(e) => setInstitutionType(e.target.value)}
                className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange"
              >
                <option value="Engineering">Engineering</option>
                <option value="Management">Management</option>
                <option value="Pharmacy">Pharmacy</option>
                <option value="Architecture">Architecture</option>
                <option value="Polytechnic">Polytechnic</option>
                <option value="Applied Arts">Applied Arts</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-primary-text mb-1">
                State <span className="text-status-error">*</span>
              </label>
              <select
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange"
              >
                <option value="Delhi">Delhi</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Karnataka">Karnataka</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Uttar Pradesh">Uttar Pradesh</option>
                <option value="Telangana">Telangana</option>
                <option value="West Bengal">West Bengal</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              City / District <span className="text-status-error">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Pune, Bengaluru, New Delhi"
              value={city}
              onChange={(e) => setCity(e.target.value)}
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
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium text-white bg-primary-orange hover:bg-primary-orange-hover rounded transition-colors shadow-xs disabled:opacity-50"
            >
              {submitting ? "Registering..." : "Register Institution"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
