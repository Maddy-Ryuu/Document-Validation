import React, { useState } from "react";
import { Upload, X, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { api } from "../services/api";

interface UploadModalProps {
  isOpen: boolean;
  applicationId: string;
  defaultCategory?: string;
  replacesDocumentId?: string;
  applicationCategory?: string;
  availableCategories?: string[];
  onClose: () => void;
  onSuccess: () => void;
}

export const EOA_CATEGORIES = [
  "Affidavit 2",
  "AICTE Portal Payment Receipt",
  "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
  "Structural Stability Certificate",
  "Fire Safety Certificate",
  "Satellite Map of Land",
  "Audited Accounts",
];

export const NON_EOA_CATEGORIES = [
  "Land Ownership and Title Certificate",
  "Land Use Certificate & Non-Encumbrance (NOC)",
  "Fire Safety NOC",
  "Approved Building Plan & Sanction Order",
  "Architect Certificate of Completion & Barrier-Free Access",
  "University Affiliation / State Govt Permission",
  "Faculty Cadre & Roster Undertaking",
  "Trust / Society Registration Deed",
  "Other Regulatory Supporting Documents",
];

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  applicationId,
  defaultCategory,
  replacesDocumentId,
  applicationCategory,
  availableCategories,
  onClose,
  onSuccess,
}) => {
  const isEoA =
    (applicationCategory || "").toLowerCase().includes("extension of approval") ||
    (applicationCategory || "").toLowerCase().includes("eoa");

  const baseCategoryList =
    availableCategories && availableCategories.length > 0
      ? availableCategories
      : isEoA
      ? EOA_CATEGORIES
      : NON_EOA_CATEGORIES;

  const categoryList =
    defaultCategory && !baseCategoryList.includes(defaultCategory)
      ? [defaultCategory, ...baseCategoryList]
      : baseCategoryList;

  const [category, setCategory] = useState(defaultCategory || categoryList[0]);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    setError(null);
    const validExtensions = ["pdf", "png", "jpg", "jpeg"];
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!ext || !validExtensions.includes(ext)) {
      setError(`Invalid format .${ext}. Only PDF, PNG, JPG, and JPEG allowed.`);
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setError("File exceeds maximum 25 MB limit.");
      return;
    }
    setFile(f);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a document file to upload.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", category);
      if (replacesDocumentId) {
        formData.append("replaces_document_id", replacesDocumentId);
      }

      await api.uploadDocument(applicationId, formData);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Upload failed. Please check file format and size.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white rounded-lg border border-border shadow-xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-surface">
          <div>
            <h2 className="text-sm font-bold text-primary-text">
              {replacesDocumentId ? "Upload Replacement Version" : "Upload Regulatory Document"}
            </h2>
            <p className="text-[11px] text-secondary-text">
              Files are securely encrypted, hashed (SHA-256) and queued for automated OCR
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-secondary-text hover:text-primary-text p-1 rounded hover:bg-surface-muted"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleUploadSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-status-error flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Category selection */}
          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Document Category <span className="text-status-error">*</span>
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full text-xs bg-white border border-border rounded px-3 py-2 text-primary-text focus:outline-none focus:border-primary-orange"
            >
              {categoryList.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Drag & Drop Box */}
          <div>
            <label className="block text-xs font-semibold text-primary-text mb-1">
              Select Document File <span className="text-status-error">*</span>
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragging
                  ? "border-primary-orange bg-orange-50/30"
                  : "border-border hover:border-primary-orange/60 bg-surface/30"
              }`}
              onClick={() => document.getElementById("file-input-upload")?.click()}
            >
              <input
                id="file-input-upload"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-8 h-8 text-primary-orange mx-auto mb-2 opacity-80" />
              {file ? (
                <div>
                  <p className="text-xs font-bold text-primary-text">{file.name}</p>
                  <p className="text-[11px] text-secondary-text mt-0.5">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for OCR processing
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-medium text-primary-text">
                    Drag and drop your PDF or image here, or <span className="text-primary-orange font-semibold">Browse</span>
                  </p>
                  <p className="text-[10px] text-secondary-text mt-1">
                    Supports digital & scanned PDF, PNG, JPG (up to 25 MB)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="pt-2 flex items-center justify-end space-x-2 border-t border-border mt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="px-4 py-2 text-xs font-medium text-secondary-text hover:text-primary-text rounded border border-border"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="px-4 py-2 text-xs font-medium text-white bg-primary-orange hover:bg-primary-orange-hover rounded shadow-xs disabled:opacity-50 flex items-center gap-1.5"
            >
              {uploading ? "Encrypting & Storing..." : "Upload & Begin OCR"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
