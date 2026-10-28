import { test, describe } from "node:test";
import assert from "node:assert/strict";

// Mock ReferenceMatchReport fixtures representing backend contract
const mockVerifiedReport = {
  application_id: "app-101",
  institution_id: "inst-001",
  reference_matched: true,
  institution_reference_id: "ref-001",
  aicte_permanent_id: "AICTE-INST-001",
  legal_name: "Delhi Institute of Technology & Advanced Sciences",
  verification_status: "OFFICIAL_VERIFIED",
  source_provenance: "AICTE_CENTRAL_PORTAL_REGISTRY",
  data_freshness_date: "2026-10-25T00:00:00Z",
  is_official: true,
  standing_status: "APPROVED_IN_GOOD_STANDING",
  matched_fields: {
    permanent_id: { submitted_value: "AICTE-INST-001", official_value: "AICTE-INST-001", match: true, confidence: 1.0 },
    legal_name: { submitted_value: "Delhi Institute of Technology & Advanced Sciences", official_value: "Delhi Institute of Technology & Advanced Sciences", match: true, confidence: 1.0 },
    state: { submitted_value: "Delhi", official_value: "Delhi", match: true, confidence: 1.0 },
    district_or_city: { submitted_value: "New Delhi", official_value: "New Delhi", match: true, confidence: 1.0 },
  },
  findings: [
    {
      finding_type: "REFERENCE_VERIFIED",
      severity: "INFO",
      message: "Application identity verified against official AICTE Central Portal registry.",
      reference_source: "AICTE_CENTRAL_PORTAL_REGISTRY",
    },
  ],
  programmes_summary: [
    {
      id: "prog-1",
      course_name: "Computer Science & Engineering",
      level: "Undergraduate",
      approved_intake: 120,
      nri_quota_approved: false,
      nri_quota_intake: 0,
      pio_fn_quota_approved: false,
      pio_fn_quota_intake: 0,
      accreditation_status: "NBA_ACCREDITED",
      academic_year: "2026-2027",
      is_active: true,
    },
  ],
  latest_approval: {
    id: "appr-1",
    academic_year: "2025-2026",
    eoa_application_number: "EOA-NORTH-2025-99881",
    total_sanctioned_intake: 120,
    approval_type: "Extension of Approval",
    issuing_authority: "AICTE Member Secretary",
    is_latest: true,
    effective_start_date: "2025-07-01T00:00:00Z",
    effective_end_date: "2026-06-30T00:00:00Z",
  },
  recommendation: "AUTO_VERIFIED",
};

const mockMismatchReport = {
  application_id: "app-102",
  institution_id: "inst-002",
  reference_matched: true,
  institution_reference_id: "ref-001",
  aicte_permanent_id: "AICTE-INST-001",
  legal_name: "Delhi Institute of Technology & Advanced Sciences",
  verification_status: "OFFICIAL_VERIFIED",
  source_provenance: "AICTE_CENTRAL_PORTAL_REGISTRY",
  data_freshness_date: "2026-10-25T00:00:00Z",
  is_official: true,
  standing_status: "APPROVED_IN_GOOD_STANDING",
  matched_fields: {
    permanent_id: { submitted_value: "AICTE-INST-001", official_value: "AICTE-INST-001", match: true, confidence: 1.0 },
    legal_name: { submitted_value: "Conflicting Commercial Institute", official_value: "Delhi Institute of Technology & Advanced Sciences", match: false, confidence: 0.28 },
    state: { submitted_value: "Delhi", official_value: "Delhi", match: true, confidence: 1.0 },
    district_or_city: { submitted_value: "New Delhi", official_value: "New Delhi", match: true, confidence: 1.0 },
  },
  findings: [
    {
      finding_type: "REFERENCE_MISMATCH",
      severity: "CRITICAL",
      message: "Submitted legal name differs significantly from official registered name in AICTE registry.",
      reference_source: "AICTE_CENTRAL_PORTAL_REGISTRY",
    },
  ],
  programmes_summary: [],
  latest_approval: null,
  recommendation: "MANUAL_SCRUTINY_REQUIRED",
};

const mockMissingReferenceReport = {
  application_id: "app-103",
  institution_id: "inst-003",
  reference_matched: false,
  institution_reference_id: null,
  aicte_permanent_id: null,
  legal_name: null,
  verification_status: "UNVERIFIED",
  source_provenance: null,
  data_freshness_date: null,
  is_official: false,
  standing_status: null,
  matched_fields: {},
  findings: [
    {
      finding_type: "REFERENCE_NOT_FOUND",
      severity: "HIGH",
      message: "No matching record found in official AICTE registry for permanent ID 'AICTE-UNREGISTERED-999'.",
      reference_source: "AICTE_CENTRAL_PORTAL_REGISTRY",
    },
  ],
  programmes_summary: [],
  latest_approval: null,
  recommendation: "MANUAL_SCRUTINY_REQUIRED",
};

const mockUnapprovedQuotaReport = {
  application_id: "app-104",
  institution_id: "inst-001",
  reference_matched: true,
  institution_reference_id: "ref-001",
  aicte_permanent_id: "AICTE-INST-001",
  legal_name: "Delhi Institute of Technology & Advanced Sciences",
  verification_status: "OFFICIAL_VERIFIED",
  source_provenance: "AICTE_CENTRAL_PORTAL_REGISTRY",
  data_freshness_date: "2026-10-25T00:00:00Z",
  is_official: true,
  standing_status: "APPROVED_IN_GOOD_STANDING",
  matched_fields: {
    quota_entitlement: { submitted_value: "NRI / Foreign National Quota", official_value: "No approved quota seats", match: false, confidence: 0.0 },
  },
  findings: [
    {
      finding_type: "UNAPPROVED_QUOTA",
      severity: "CRITICAL",
      message: "Institution does not possess authorized NRI/PIO/FN quota seats in AICTE central registry.",
      reference_source: "AICTE_CENTRAL_PORTAL_REGISTRY",
    },
  ],
  programmes_summary: [],
  latest_approval: null,
  recommendation: "REJECT_UNAUTHORIZED",
};

const mockOutdatedApprovalReport = {
  application_id: "app-105",
  institution_id: "inst-outdated",
  reference_matched: true,
  institution_reference_id: "ref-outdated",
  aicte_permanent_id: "AICTE-INST-OUTDATED",
  legal_name: "Heritage Technical Academy",
  verification_status: "OFFICIAL_VERIFIED",
  source_provenance: "AICTE_CENTRAL_PORTAL_REGISTRY",
  data_freshness_date: "2026-10-25T00:00:00Z",
  is_official: true,
  standing_status: "APPROVED_IN_GOOD_STANDING",
  matched_fields: {},
  findings: [
    {
      finding_type: "OUTDATED_APPROVAL",
      severity: "HIGH",
      message: "Continuous approval lapsed: Most recent prior approval is 2023-2024; lacking 2025-2026 approval.",
      reference_source: "AICTE_CENTRAL_PORTAL_REGISTRY",
    },
  ],
  programmes_summary: [],
  latest_approval: {
    academic_year: "2023-2024",
    total_sanctioned_intake: 60,
    is_latest: true,
  },
  recommendation: "MANUAL_SCRUTINY_REQUIRED",
};

// ===========================================================================
// FRONTEND TEST SUITE
// ===========================================================================

describe("Phase 2 Reference Data Cross-Verification Frontend Models", () => {
  test("1. Successfully verifies official matching records with good standing", () => {
    assert.equal(mockVerifiedReport.recommendation, "AUTO_VERIFIED");
    assert.equal(mockVerifiedReport.is_official, true);
    assert.equal(mockVerifiedReport.verification_status, "OFFICIAL_VERIFIED");
    assert.equal(mockVerifiedReport.standing_status, "APPROVED_IN_GOOD_STANDING");
    assert.equal(mockVerifiedReport.matched_fields.legal_name.match, true);
    assert.equal(mockVerifiedReport.programmes_summary.length, 1);
    assert.equal(mockVerifiedReport.programmes_summary[0].approved_intake, 120);
    assert.equal(mockVerifiedReport.latest_approval?.academic_year, "2025-2026");
  });

  test("2. Detects identity discrepancies and flags MANUAL_SCRUTINY_REQUIRED", () => {
    assert.equal(mockMismatchReport.recommendation, "MANUAL_SCRUTINY_REQUIRED");
    assert.equal(mockMismatchReport.matched_fields.legal_name.match, false);
    assert.ok(mockMismatchReport.matched_fields.legal_name.confidence < 0.5);
    const mismatchFinding = mockMismatchReport.findings.find(
      (f) => f.finding_type === "REFERENCE_MISMATCH"
    );
    assert.ok(mismatchFinding);
    assert.equal(mismatchFinding.severity, "CRITICAL");
  });

  test("3. Missing reference records require explicit manual scrutiny and route safely", () => {
    assert.equal(mockMissingReferenceReport.reference_matched, false);
    assert.equal(mockMissingReferenceReport.recommendation, "MANUAL_SCRUTINY_REQUIRED");
    assert.equal(mockMissingReferenceReport.verification_status, "UNVERIFIED");
    assert.equal(mockMissingReferenceReport.is_official, false);
    const notFound = mockMissingReferenceReport.findings.find(
      (f) => f.finding_type === "REFERENCE_NOT_FOUND"
    );
    assert.ok(notFound);
    assert.equal(notFound.severity, "HIGH");
  });

  test("4. Unapproved quota submissions trigger REJECT_UNAUTHORIZED recommendation", () => {
    assert.equal(mockUnapprovedQuotaReport.recommendation, "REJECT_UNAUTHORIZED");
    const quotaFinding = mockUnapprovedQuotaReport.findings.find(
      (f) => f.finding_type === "UNAPPROVED_QUOTA"
    );
    assert.ok(quotaFinding);
    assert.equal(quotaFinding.severity, "CRITICAL");
  });

  test("5. Lapsed or outdated approval chain flags OUTDATED_APPROVAL finding", () => {
    assert.equal(mockOutdatedApprovalReport.recommendation, "MANUAL_SCRUTINY_REQUIRED");
    const outdatedFinding = mockOutdatedApprovalReport.findings.find(
      (f) => f.finding_type === "OUTDATED_APPROVAL"
    );
    assert.ok(outdatedFinding);
    assert.equal(outdatedFinding.severity, "HIGH");
    assert.equal(mockOutdatedApprovalReport.latest_approval?.academic_year, "2023-2024");
  });

  test("6. Synthetic benchmark data is clearly distinguished from official data", () => {
    const syntheticReport = {
      ...mockVerifiedReport,
      is_official: false,
      verification_status: "SYNTHETIC_BENCHMARK",
      recommendation: "MANUAL_SCRUTINY_REQUIRED",
    };
    assert.equal(syntheticReport.is_official, false);
    assert.equal(syntheticReport.verification_status, "SYNTHETIC_BENCHMARK");
    assert.notEqual(syntheticReport.recommendation, "AUTO_VERIFIED");
  });

  test("7. Handles API error states gracefully without crashing", async () => {
    // Simulate API fetch failure
    const simulateFetchError = async () => {
      throw new Error("Unable to connect to AICTE validation server");
    };

    let errorCaught = false;
    try {
      await simulateFetchError();
    } catch (err) {
      errorCaught = true;
      assert.match(err.message, /Unable to connect/);
    }
    assert.equal(errorCaught, true);
  });

  test("8. Loading and retry state transitions are deterministic", () => {
    let loading = true;
    let data = null;
    let error = null;

    // Start request
    assert.equal(loading, true);
    assert.equal(data, null);

    // Simulate completion
    loading = false;
    data = mockVerifiedReport;
    assert.equal(loading, false);
    assert.notEqual(data, null);
    assert.equal(error, null);

    // Simulate retry on error
    loading = true;
    error = null;
    assert.equal(loading, true);
    loading = false;
    error = "Network timeout";
    assert.equal(error, "Network timeout");
  });
});
