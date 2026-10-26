import React, { useState, useEffect } from "react";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Eye,
  Download,
  RotateCw,
  Edit2,
  Check,
  X,
  ExternalLink,
  ShieldCheck,
  ChevronRight,
  History,
} from "lucide-react";
import { api } from "../services/api";
import { DocumentItem, DocumentExtraction, DocumentFieldExtraction } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate, formatDateTime } from "../lib/utils";

interface DocumentViewerProps {
  document: DocumentItem;
  onClose: () => void;
  onRefresh: () => void;
  onReplace: (doc: DocumentItem) => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  document: doc,
  onClose,
  onRefresh,
  onReplace,
}) => {
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [versions, setVersions] = useState<DocumentItem[]>([]);
  const [loadingExtraction, setLoadingExtraction] = useState(true);
  const [reprocessing, setReprocessing] = useState(false);
  const [activeTab, setActiveTab] = useState<"fields" | "text" | "versions">("fields");

  // Editing field state
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [editReason, setEditReason] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  useEffect(() => {
    loadExtractionAndVersions();
  }, [doc.id]);

  const loadExtractionAndVersions = async () => {
    setLoadingExtraction(true);
    try {
      const [ext, vers] = await Promise.all([
        api.getDocumentExtraction(doc.id).catch(() => null),
        api.getDocumentVersions(doc.id).catch(() => [doc]),
      ]);
      setExtraction(ext);
      setVersions(vers || [doc]);
    } catch {
      // Handled
    } finally {
      setLoadingExtraction(false);
    }
  };

  const handleReprocess = async () => {
    setReprocessing(true);
    try {
      await api.triggerDocumentProcess(doc.id);
      setTimeout(() => {
        loadExtractionAndVersions();
        onRefresh();
        setReprocessing(false);
      }, 1500);
    } catch (err: any) {
      alert(`Reprocessing trigger failed: ${err.message}`);
      setReprocessing(false);
    }
  };

  const handleStartEdit = (fieldName: string, currentVal: string) => {
    setEditingField(fieldName);
    setEditValue(currentVal || "");
    setEditReason("");
  };

  const handleSaveEdit = async (fieldName: string) => {
    if (!editValue.trim()) return;
    setSavingEdit(true);
    try {
      const updated = await api.correctDocumentField(
        doc.id,
        fieldName,
        editValue.trim(),
        editReason.trim() || "Manual scrutiny officer correction"
      );
      setExtraction(updated);
      setEditingField(null);
      onRefresh();
    } catch (err: any) {
      alert(`Failed to save correction: ${err.message}`);
    } finally {
      setSavingEdit(false);
    }
  };

  const fileUrl = api.getDocumentFileUrl(doc.id);
  const isPdf = doc.original_filename.toLowerCase().endsWith(".pdf");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white rounded-xl border border-border shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="px-6 py-3.5 border-b border-border flex items-center justify-between bg-surface">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-primary-orange/10 flex items-center justify-center text-primary-orange">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-primary-text">{doc.original_filename}</h2>
                <StatusBadge status={doc.processing_status} />
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-border text-secondary-text">
                  v{doc.version}
                </span>
              </div>
              <p className="text-[11px] text-secondary-text">{doc.document_type}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onReplace(doc)}
              className="px-2.5 py-1.5 bg-white border border-border text-xs rounded hover:bg-surface text-secondary-text font-medium flex items-center gap-1"
            >
              Replace Version
            </button>
            <a
              href={fileUrl}
              download={doc.original_filename}
              target="_blank"
              rel="noreferrer"
              className="p-1.5 bg-white border border-border text-secondary-text hover:text-primary-text rounded hover:bg-surface"
              title="Download Original"
            >
              <Download className="w-4 h-4" />
            </a>
            <button
              onClick={handleReprocess}
              disabled={reprocessing}
              className="p-1.5 bg-white border border-border text-secondary-text hover:text-primary-text rounded hover:bg-surface"
              title="Re-run OCR Extraction"
            >
              <RotateCw className={`w-4 h-4 ${reprocessing ? "animate-spin text-primary-orange" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-secondary-text hover:text-primary-text rounded hover:bg-surface-muted"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 2-Column Main Workspace */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 divide-x divide-border overflow-hidden">
          {/* Left Column: Original Document Preview */}
          <div className="h-full flex flex-col bg-surface/30 overflow-hidden">
            <div className="px-4 py-2 border-b border-border bg-white text-xs font-semibold text-secondary-text flex items-center justify-between">
              <span>Original Document Preview</span>
              <a
                href={fileUrl}
                target="_blank"
                rel="noreferrer"
                className="text-primary-orange hover:underline text-[11px] inline-flex items-center gap-1"
              >
                Open in tab <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="flex-1 p-2 overflow-auto flex items-center justify-center">
              {isPdf ? (
                <iframe
                  src={`${fileUrl}#toolbar=0`}
                  title="PDF Preview"
                  className="w-full h-full rounded border border-border bg-white shadow-xs"
                />
              ) : (
                <img
                  src={fileUrl}
                  alt="Scanned Preview"
                  className="max-h-full max-w-full object-contain rounded shadow-xs"
                />
              )}
            </div>

            {/* SHA-256 Footer */}
            <div className="p-2.5 border-t border-border bg-white text-[10px] text-secondary-text font-mono truncate">
              <span className="font-semibold text-primary-text">SHA-256:</span> {doc.sha256_hash || "Computing"}
            </div>
          </div>

          {/* Right Column: OCR & Extracted Information Inspector */}
          <div className="h-full flex flex-col bg-white overflow-hidden">
            {/* Tabs */}
            <div className="px-4 py-2 border-b border-border bg-surface/40 flex items-center justify-between">
              <div className="flex space-x-1">
                <button
                  onClick={() => setActiveTab("fields")}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    activeTab === "fields"
                      ? "bg-white text-primary-orange shadow-xs border border-border"
                      : "text-secondary-text hover:text-primary-text"
                  }`}
                >
                  Structured Fields
                </button>
                <button
                  onClick={() => setActiveTab("text")}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    activeTab === "text"
                      ? "bg-white text-primary-orange shadow-xs border border-border"
                      : "text-secondary-text hover:text-primary-text"
                  }`}
                >
                  Raw OCR Text
                </button>
                <button
                  onClick={() => setActiveTab("versions")}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    activeTab === "versions"
                      ? "bg-white text-primary-orange shadow-xs border border-border"
                      : "text-secondary-text hover:text-primary-text"
                  }`}
                >
                  Version History ({versions.length})
                </button>
              </div>

              {extraction && (
                <div className="text-[11px] text-secondary-text flex items-center gap-1">
                  <span>Confidence:</span>
                  <span className="font-bold text-status-success">
                    {Math.round((extraction.confidence_score || 0.9) * 100)}%
                  </span>
                </div>
              )}
            </div>

            {/* Tab Contents */}
            <div className="flex-1 overflow-y-auto p-5">
              {loadingExtraction ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-12 bg-surface animate-pulse rounded" />
                  ))}
                </div>
              ) : activeTab === "fields" ? (
                <div className="space-y-4">
                  {!extraction || !extraction.structured_fields || Object.keys(extraction.structured_fields).length === 0 ? (
                    <div className="p-8 text-center text-xs text-secondary-text border border-dashed border-border rounded-lg">
                      <Clock className="w-6 h-6 text-secondary-text/50 mx-auto mb-2" />
                      <p className="font-semibold text-primary-text">No structured fields extracted</p>
                      <p className="mt-1">
                        Run OCR extraction or review raw text tab to verify document content.
                      </p>
                    </div>
                  ) : (
                    Object.entries(extraction.structured_fields).map(([fieldKey, f]: [string, DocumentFieldExtraction]) => {
                      const isEditing = editingField === fieldKey;

                      return (
                        <div
                          key={fieldKey}
                          className="p-3 rounded-lg border border-border bg-surface/30 hover:bg-surface/50 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[11px] font-semibold text-secondary-text uppercase tracking-wider">
                              {fieldKey.replace(/_/g, " ")}
                            </span>
                            <div className="flex items-center space-x-1.5">
                              {f.corrected ? (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-medium border border-blue-200">
                                  Officer Corrected
                                </span>
                              ) : (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-50 text-status-success font-medium border border-green-200">
                                  Auto-Extracted ({Math.round((f.confidence || 0.9) * 100)}%)
                                </span>
                              )}

                              {!isEditing && (
                                <button
                                  onClick={() => handleStartEdit(fieldKey, f.value)}
                                  className="text-secondary-text hover:text-primary-orange p-1"
                                  title="Edit / Correct Value"
                                >
                                  <Edit2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </div>
                          </div>

                          {isEditing ? (
                            <div className="space-y-2 mt-2 pt-2 border-t border-border">
                              <div>
                                <label className="text-[10px] text-secondary-text block">Corrected Value</label>
                                <input
                                  type="text"
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="w-full text-xs bg-white border border-border rounded px-2.5 py-1.5 focus:border-primary-orange focus:outline-none"
                                />
                              </div>
                              <div>
                                <label className="text-[10px] text-secondary-text block">Audit Note / Reason</label>
                                <input
                                  type="text"
                                  placeholder="e.g. Typo in OCR or verified with official gazette"
                                  value={editReason}
                                  onChange={(e) => setEditReason(e.target.value)}
                                  className="w-full text-xs bg-white border border-border rounded px-2.5 py-1.5 focus:border-primary-orange focus:outline-none"
                                />
                              </div>
                              <div className="flex justify-end space-x-1.5 pt-1">
                                <button
                                  onClick={() => setEditingField(null)}
                                  className="px-2.5 py-1 text-xs border border-border rounded bg-white"
                                >
                                  Cancel
                                </button>
                                <button
                                  onClick={() => handleSaveEdit(fieldKey)}
                                  disabled={savingEdit}
                                  className="px-3 py-1 text-xs bg-primary-orange text-white rounded font-medium"
                                >
                                  {savingEdit ? "Saving..." : "Save Correction"}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <p className="text-xs font-bold text-primary-text">{f.value}</p>
                              {f.source_snippet && (
                                <p className="text-[11px] text-secondary-text italic mt-1 bg-white p-2 rounded border border-border">
                                  &quot;{f.source_snippet}&quot;
                                </p>
                              )}
                              {f.original_extracted_value && (
                                <p className="text-[10px] text-secondary-text mt-1">
                                  Original OCR: <span className="line-through">{f.original_extracted_value}</span>
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              ) : activeTab === "text" ? (
                <div className="bg-surface/50 p-4 rounded border border-border font-mono text-xs whitespace-pre-wrap leading-relaxed text-primary-text">
                  {extraction?.raw_text || "No raw text available."}
                </div>
              ) : (
                <div className="space-y-3">
                  {versions.map((v) => (
                    <div
                      key={v.id}
                      className={`p-3 rounded-lg border text-xs ${
                        v.id === doc.id
                          ? "border-primary-orange bg-orange-50/20"
                          : "border-border bg-white"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-primary-text">
                          Version {v.version} {v.id === doc.id ? "(Current)" : ""}
                        </span>
                        <StatusBadge status={v.processing_status} />
                      </div>
                      <p className="text-[11px] text-secondary-text mt-1">{v.original_filename}</p>
                      <p className="text-[10px] text-secondary-text font-mono mt-0.5">
                        Uploaded: {formatDateTime(v.created_at)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
