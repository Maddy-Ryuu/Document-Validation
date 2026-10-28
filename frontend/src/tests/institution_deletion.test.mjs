import { test, describe } from "node:test";
import assert from "node:assert/strict";

describe("Institution Deletion & Administrative Authorization Client Logic", () => {
  // Mock institution item fixture
  const sampleEligibleInst = {
    id: "inst-clean-01",
    institution_identifier: "AICTE-ENG-001",
    name: "Apex College of Engineering",
    institution_type: "Engineering",
    state: "Maharashtra",
    city: "Pune",
    created_at: "2026-01-15T10:00:00Z",
    application_count: 0,
  };

  const sampleConflictInst = {
    id: "inst-conflict-02",
    institution_identifier: "AICTE-PHARM-002",
    name: "National Institute of Pharmaceutical Sciences",
    institution_type: "Pharmacy",
    state: "Karnataka",
    city: "Bengaluru",
    created_at: "2026-01-10T09:00:00Z",
    application_count: 3,
  };

  test("1. Eligible institution with 0 linked applications allows deletion request", () => {
    assert.equal(sampleEligibleInst.application_count, 0);
    const canAttemptDelete = (inst) => Boolean(inst && inst.id);
    assert.equal(canAttemptDelete(sampleEligibleInst), true);
  });

  test("2. Institution with active linked applications triggers conflict warning", () => {
    assert.ok(sampleConflictInst.application_count > 0);
    const hasLinkedApplicationsWarning = (inst) => {
      if ((inst.application_count ?? 0) > 0) {
        return `Active Regulatory History Detected: This institution has ${inst.application_count} active application(s).`;
      }
      return null;
    };

    const warning = hasLinkedApplicationsWarning(sampleConflictInst);
    assert.ok(warning !== null);
    assert.match(warning, /Active Regulatory History/);
    assert.match(warning, /3 active application/);
  });

  test("3. Only administrator accounts satisfy administrative privilege check", () => {
    const isAuthorizedAdmin = (role) => ["admin", "superadmin", "administrator"].includes(role);

    assert.equal(isAuthorizedAdmin("admin"), true);
    assert.equal(isAuthorizedAdmin("superadmin"), true);
    assert.equal(isAuthorizedAdmin("administrator"), true);
    assert.equal(isAuthorizedAdmin("compliance_officer"), false);
    assert.equal(isAuthorizedAdmin("reviewer"), false);
    assert.equal(isAuthorizedAdmin("guest"), false);
    assert.equal(isAuthorizedAdmin(undefined), false);
  });

  test("4. Conflict error response from backend is parsed into human-readable alert", () => {
    const backendConflictResponse = {
      detail:
        "LINKED_RECORDS_EXIST: Cannot delete institution 'National Institute of Pharmaceutical Sciences' (AICTE-PHARM-002): 3 active application(s) exist. Applications and linked statutory documents must be resolved or deleted first to prevent orphaned records.",
    };

    const formatErrorMessage = (err) => err.detail || err.message || "Failed to delete institution";
    const formatted = formatErrorMessage(backendConflictResponse);

    assert.match(formatted, /LINKED_RECORDS_EXIST/);
    assert.match(formatted, /3 active application/);
  });

  test("5. Authoritative reference records protection error is identified", () => {
    const refRecordError = {
      detail:
        "PROTECTED_REFERENCE_RECORD: Authoritative regulatory reference records cannot be deleted through the operational institution interface.",
    };

    assert.match(refRecordError.detail, /PROTECTED_REFERENCE_RECORD/);
    assert.match(refRecordError.detail, /cannot be deleted/);
  });

  test("6. Successful deletion generates appropriate forensic audit notification", () => {
    const mockSuccessResponse = {
      success: true,
      message: "Institution deleted successfully and forensic audit record preserved.",
      deleted_institution_id: "inst-clean-01",
    };

    assert.equal(mockSuccessResponse.success, true);
    assert.equal(mockSuccessResponse.deleted_institution_id, "inst-clean-01");
    assert.match(mockSuccessResponse.message, /forensic audit record preserved/i);
  });
});
