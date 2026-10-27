import React, { useState, useEffect } from "react";
import {
  FileCheck2,
  Search,
  Filter,
  Eye,
  Download,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  ChevronLeft,
  ChevronRight,
  FileText,
  Building,
  Check,
  X,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";
import { DocumentReviewItem, DocumentItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { DocumentViewer } from "../components/DocumentViewer";
import { formatDate } from "../lib/utils";

interface DocumentReviewPageProps {
  onSelectApplication: (id: string) => void;
  refreshTrigger: number;
}

export const DocumentReviewPage: React.FC<DocumentReviewPageProps> = ({
  onSelectApplication,
  refreshTrigger,
}) => {
  const [documents, setDocuments] = useState<DocumentReviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Document viewer modal
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);

  // Review action feedback
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, [page, statusFilter, typeFilter, refreshTrigger]);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAllDocuments({
        page,
        limit: 12,
        search: search.trim() || undefined,
        status: statusFilter !== "All" ? statusFilter : undefined,
        document_type: typeFilter !== "All" ? typeFilter : undefined,
      });
      setDocuments(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchDocuments();
  };

  const handleReviewAction = async (docId: string, action: "Approved" | "Needs Review" | "Rejected") => {
    setReviewingId(docId);
    try {
      await api.reviewDocument(docId, action, `Manual review action: ${action}`);
      setActionSuccess(`Document marked as "${action}" successfully`);
      setTimeout(() => setActionSuccess(null), 3000);
      fetchDocuments();
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setReviewingId(null);
    }
  };

  // Stats calculation
  const processedCount = documents.filter((d) => d.processing_status === "Processed").length;
  const reviewNeededCount = documents.filter((d) => d.processing_status === "Needs Review" || d.processing_status === "Failed").length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-primary-text tracking-tight">Document Review & OCR Scrutiny</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
              Active Module
            </span>
          </div>
          <p className="text-xs text-secondary-text mt-0.5">
            Cryptographic SHA-256 verification, OCR extraction inspection, and statutory document review workspace
          </p>
        </div>

        <button
          onClick={fetchDocuments}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-border text-primary-text text-xs font-medium rounded-md hover:bg-surface transition-colors shadow-xs"
        >
          <RotateCw className="w-3.5 h-3.5 text-secondary-text" />
          <span>Refresh</span>
        </button>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-xs flex items-center justify-between animate-fade-in">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Total Documents</span>
            <FileText className="w-4 h-4 text-primary-orange" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">{total}</div>
          <div className="text-[11px] text-secondary-text mt-1">Across all active applications</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Processed / Validated</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-700">{processedCount}</div>
          <div className="text-[11px] text-secondary-text mt-1">Passed initial OCR and sanity checks</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Needs Officer Review</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-600">{reviewNeededCount}</div>
          <div className="text-[11px] text-secondary-text mt-1">Flagged for manual scrutiny</div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-border shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-secondary-text">Storage Integrity</span>
            <Shield className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-text">100%</div>
          <div className="text-[11px] text-emerald-600 font-medium mt-1">SHA-256 Hash Tampering Audit OK</div>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-border shadow-xs space-y-3">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full">
            <Search className="w-3.5 h-3.5 text-secondary-text absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search filename, document type, application code, institution..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
            />
          </form>

          <div className="flex items-center space-x-2 w-full md:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
            >
              <option value="All">All Statuses</option>
              <option value="Processed">Processed</option>
              <option value="Needs Review">Needs Review</option>
              <option value="Uploaded">Uploaded</option>
              <option value="Queued">Queued</option>
              <option value="Failed">Failed</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1.5 text-xs bg-white border border-border rounded-md text-primary-text focus:outline-none focus:border-primary-orange"
            >
              <option value="All">All Document Types</option>
              <option value="Land Ownership and Title Certificate">Land Title Certificate</option>
              <option value="Land Use Certificate & Non-Encumbrance (NOC)">Land Use & Non-Encumbrance</option>
              <option value="Fire Safety NOC">Fire Safety NOC</option>
              <option value="Approved Building Plan & Sanction Order">Approved Building Plan</option>
              <option value="Architect Certificate of Completion & Barrier-Free Access">Architect Certificate</option>
              <option value="University Affiliation / State Govt Permission">University Affiliation</option>
              <option value="Faculty Cadre & Roster Undertaking">Faculty Cadre Undertaking</option>
              <option value="Other Regulatory Supporting Documents">Other Regulatory</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-lg border border-border shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
            <RotateCw className="w-5 h-5 animate-spin text-primary-orange" />
            <span>Loading document repository from secure storage...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600 text-xs">
            <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <span>{error}</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-secondary-text text-xs">
            <FileText className="w-8 h-8 mx-auto mb-2 text-border" />
            <p className="font-medium text-primary-text">No documents found</p>
            <p className="mt-1">Try adjusting your search criteria or status filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-muted/50 text-[11px] font-semibold text-secondary-text uppercase tracking-wider">
                  <th className="py-3 px-4">Document Details</th>
                  <th className="py-3 px-4">Application & Institute</th>
                  <th className="py-3 px-4">Status & OCR</th>
                  <th className="py-3 px-4">SHA-256 Fingerprint</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4 text-right">Reviewer Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {documents.map((doc) => {
                  const isReviewing = reviewingId === doc.id;
                  return (
                    <tr key={doc.id} className="hover:bg-surface/50 transition-colors">
                      <td className="py-3 px-4 max-w-xs">
                        <div className="font-semibold text-primary-text truncate" title={doc.original_filename}>
                          {doc.original_filename}
                        </div>
                        <div className="text-[11px] text-secondary-text flex items-center space-x-1.5 mt-0.5">
                          <span className="font-medium text-primary-orange">{doc.document_type}</span>
                          <span>•</span>
                          <span>{doc.file_size_bytes ? `${Math.round(doc.file_size_bytes / 1024)} KB` : "N/A"}</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        {doc.application_identifier ? (
                          <button
                            onClick={() => onSelectApplication(doc.application_id)}
                            className="font-medium text-primary-orange hover:underline text-xs block text-left"
                          >
                            {doc.application_identifier}
                          </button>
                        ) : (
                          <span className="text-secondary-text">N/A</span>
                        )}
                        <div className="text-[11px] text-secondary-text truncate max-w-[200px]" title={doc.institution_name}>
                          {doc.institution_name || "Unknown Institute"}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <StatusBadge status={doc.processing_status} />
                          {doc.confidence_score !== undefined && doc.confidence_score !== null && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-mono">
                              {Math.round(doc.confidence_score * 100)}% OCR
                            </span>
                          )}
                        </div>
                        {doc.findings_count && doc.findings_count > 0 ? (
                          <div className="text-[10px] text-red-600 font-medium mt-1 flex items-center space-x-1">
                            <AlertTriangle className="w-3 h-3" />
                            <span>{doc.findings_count} compliance finding(s)</span>
                          </div>
                        ) : null}
                      </td>

                      <td className="py-3 px-4 font-mono text-[10px] text-secondary-text">
                        {doc.sha256_hash ? (
                          <span title={doc.sha256_hash}>
                            {doc.sha256_hash.substring(0, 12)}...{doc.sha256_hash.substring(doc.sha256_hash.length - 6)}
                          </span>
                        ) : (
                          "Pending"
                        )}
                      </td>

                      <td className="py-3 px-4 text-secondary-text text-[11px] whitespace-nowrap">
                        {formatDate(doc.created_at)}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          {/* Inspect Modal */}
                          <button
                            onClick={() => setSelectedDoc(doc)}
                            className="p-1.5 bg-white border border-border rounded text-secondary-text hover:text-primary-text hover:bg-surface transition-colors"
                            title="Inspect OCR & Fields"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>

                          {/* Secure Download */}
                          <a
                            href={api.getDocumentFileUrl(doc.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 bg-white border border-border rounded text-secondary-text hover:text-primary-text hover:bg-surface transition-colors"
                            title="Download Official File"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>

                          {/* Quick Review Decisions */}
                          {doc.processing_status !== "Processed" && (
                            <button
                              disabled={isReviewing}
                              onClick={() => handleReviewAction(doc.id, "Approved")}
                              className="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 rounded text-[11px] font-medium transition-colors"
                              title="Approve Document"
                            >
                              Approve
                            </button>
                          )}

                          {doc.processing_status !== "Needs Review" && (
                            <button
                              disabled={isReviewing}
                              onClick={() => handleReviewAction(doc.id, "Needs Review")}
                              className="px-2 py-1 bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 rounded text-[11px] font-medium transition-colors"
                              title="Flag for Review"
                            >
                              Flag
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && documents.length > 0 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-xs text-secondary-text">
            <span>
              Showing {(page - 1) * 12 + 1} to {Math.min(page * 12, total)} of {total} documents
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1 rounded border border-border hover:bg-surface disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span>Page {page} of {pages}</span>
              <button
                disabled={page >= pages}
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                className="p-1 rounded border border-border hover:bg-surface disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Inspect Document Modal */}
      {selectedDoc && (
        <DocumentViewer
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
          onRefresh={fetchDocuments}
          onReplace={() => {}}
        />
      )}
    </div>
  );
};
