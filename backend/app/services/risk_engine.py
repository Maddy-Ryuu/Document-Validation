"""
risk_engine.py
Deterministic, configurable risk scoring engine for AICTE applications.
Evaluates compliance findings, document authentications, and evidence completeness,
yielding explainable factor breakdowns, completeness statuses, and audit records.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import (
    Application,
    Document,
    ValidationRun,
    Finding,
    RiskAssessment,
    AuditEvent,
)
from app.core.risk_config import (
    RISK_SCORING_VERSION,
    DEFAULT_RISK_WEIGHTS,
    RISK_BANDS,
    COMPLETENESS_COMPLETE,
    COMPLETENESS_INCOMPLETE,
    COMPLETENESS_REQUIRES_REVIEW,
)
from app.core.regulatory_rules import RULE_REGISTRY


class RiskScoringEngine:
    @staticmethod
    def evaluate_application_risk(
        db: Session,
        application_id: str,
        weights: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates and persists a deterministic risk assessment for an application
        using its latest compliance run, findings, and uploaded evidence.
        """
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        active_weights = {**DEFAULT_RISK_WEIGHTS, **(weights or {})}

        # Retrieve latest ValidationRun
        latest_run = (
            db.query(ValidationRun)
            .filter(ValidationRun.application_id == app.id)
            .order_by(desc(ValidationRun.started_at))
            .first()
        )

        if not latest_run:
            raise ValueError(
                f"No compliance evaluation has been executed for application {app.application_identifier}. "
                f"Please run the compliance engine before calculating risk."
            )

        # Retrieve findings strictly associated with this application and source run
        findings = (
            db.query(Finding)
            .filter(
                Finding.application_id == app.id,
                Finding.validation_run_id == latest_run.id,
            )
            .all()
        )

        # Documents
        docs = db.query(Document).filter(Document.application_id == app.id).all()

        contributing_factors: List[Dict[str, Any]] = []
        missing_evidence_items: List[str] = []
        unresolved_reviews: List[str] = []

        total_risk_score = 0

        # Group findings by rule_code to deduplicate and prevent double-counting
        findings_by_rule: Dict[str, List[Finding]] = {}
        for f in findings:
            code = f.rule_code or "UNKNOWN"
            if code not in findings_by_rule:
                findings_by_rule[code] = []
            findings_by_rule[code].append(f)

        # Factor A: Expired Regulatory Documents (APH-RULE-DOC-EXPIRY failures)
        expiry_findings = findings_by_rule.get("APH-RULE-DOC-EXPIRY", [])
        expired_failures = [f for f in expiry_findings if "expired" in f.title.lower() or "expired" in f.explanation.lower()]
        if expired_failures:
            f = expired_failures[0]
            pts = active_weights["EXPIRED_REGULATORY_DOCUMENTS"]
            total_risk_score += pts
            contributing_factors.append({
                "factor_code": "EXPIRED_REGULATORY_DOCUMENTS",
                "factor_name": "Expired Regulatory Clearance / Statutory Certificate",
                "points": pts,
                "rule_code": "APH-RULE-DOC-EXPIRY",
                "finding_id": f.id,
                "evidence_reference": f.evidence_reference or f.title,
                "reason": f.explanation,
                "severity": "CRITICAL",
            })

        # Factor B: Cross-Document Identity Inconsistencies (APH-RULE-CROSS-ID-MISMATCH failures)
        cross_id_findings = findings_by_rule.get("APH-RULE-CROSS-ID-MISMATCH", [])
        mismatch_failures = [f for f in cross_id_findings if "mismatch" in f.title.lower() or "mismatch" in f.explanation.lower()]
        if mismatch_failures:
            f = mismatch_failures[0]
            pts = active_weights["CROSS_DOCUMENT_INCONSISTENCIES"]
            total_risk_score += pts
            contributing_factors.append({
                "factor_code": "CROSS_DOCUMENT_INCONSISTENCIES",
                "factor_name": "Cross-Document Institutional Identity Inconsistencies",
                "points": pts,
                "rule_code": "APH-RULE-CROSS-ID-MISMATCH",
                "finding_id": f.id,
                "evidence_reference": f.evidence_reference or f.title,
                "reason": f.explanation,
                "severity": "CRITICAL",
            })

        # Factor C: Missing Mandatory Evidence / Documents (APH-RULE-DOC-CHECKLIST failures)
        checklist_findings = findings_by_rule.get("APH-RULE-DOC-CHECKLIST", [])
        if checklist_findings:
            f = checklist_findings[0]
            pts = active_weights["MISSING_REQUIRED_EVIDENCE"]
            total_risk_score += pts
            missing_evidence_items.append(f.explanation)
            contributing_factors.append({
                "factor_code": "MISSING_REQUIRED_EVIDENCE",
                "factor_name": "Missing Mandatory Statutory Evidence",
                "points": pts,
                "rule_code": "APH-RULE-DOC-CHECKLIST",
                "finding_id": f.id,
                "evidence_reference": f.evidence_reference or f.title,
                "reason": f.explanation,
                "severity": "CRITICAL",
            })

        # Factor D: Unverified Document Authenticity (Synthetic / metadata summaries)
        # Note: Avoid double counting if already penalized as expired
        unverified_findings = [
            f for f in findings
            if "unverified" in f.title.lower() or "synthetic" in f.title.lower()
        ]
        if unverified_findings:
            # Dedup across documents
            seen_unverified_rules = set()
            for f in unverified_findings:
                if f.rule_code in seen_unverified_rules:
                    continue
                seen_unverified_rules.add(f.rule_code)
                pts = active_weights["UNVERIFIED_DOCUMENT_AUTHENTICITY"]
                total_risk_score += pts
                unresolved_reviews.append(f.title)
                contributing_factors.append({
                    "factor_code": "UNVERIFIED_DOCUMENT_AUTHENTICITY",
                    "factor_name": f"Unverified Certificate Authenticity ({f.rule_code})",
                    "points": pts,
                    "rule_code": f.rule_code,
                    "finding_id": f.id,
                    "evidence_reference": f.evidence_reference or f.title,
                    "reason": f.explanation,
                    "severity": f.severity,
                })

        # Factor E: Other Critical or Major Compliance Failures not already penalized above
        specialized_rules = {"APH-RULE-DOC-EXPIRY", "APH-RULE-CROSS-ID-MISMATCH", "APH-RULE-DOC-CHECKLIST"}
        for f in findings:
            if f.rule_code in specialized_rules or f in unverified_findings:
                continue

            sev_upper = f.severity.upper()
            if sev_upper == "CRITICAL":
                pts = active_weights["CRITICAL_COMPLIANCE_FAILURE"]
            elif sev_upper == "HIGH":
                pts = active_weights["MAJOR_COMPLIANCE_FAILURE"]
            elif sev_upper in ["MEDIUM", "LOW"]:
                pts = active_weights["MINOR_COMPLIANCE_FAILURE"]
            else:
                pts = active_weights["MINOR_COMPLIANCE_FAILURE"]

            total_risk_score += pts
            contributing_factors.append({
                "factor_code": f"{sev_upper}_COMPLIANCE_FAILURE",
                "factor_name": f"{sev_upper.title()} Compliance Failure ({f.rule_code or 'General'})",
                "points": pts,
                "rule_code": f.rule_code,
                "finding_id": f.id,
                "evidence_reference": f.evidence_reference or f.title,
                "reason": f.explanation,
                "severity": f.severity,
            })

        # Deterministic clamping: 0 <= score <= 100
        final_score = max(0.0, min(100.0, float(total_risk_score)))

        # Determine Risk Band
        if final_score <= RISK_BANDS["LOW"]["max"]:
            risk_band = "Low"
        elif final_score <= RISK_BANDS["MEDIUM"]["max"]:
            risk_band = "Medium"
        else:
            risk_band = "High"

        # Determine Assessment Completeness Status
        if len(docs) == 0:
            completeness = COMPLETENESS_INCOMPLETE
            missing_evidence_items.append("No document files uploaded in application dossier.")
        elif any("unverified" in f.title.lower() for f in findings):
            completeness = COMPLETENESS_REQUIRES_REVIEW
        elif any(f.rule_code == "APH-RULE-DOC-CHECKLIST" for f in findings):
            completeness = COMPLETENESS_INCOMPLETE
        elif any(f.severity in ["Medium", "High", "MEDIUM", "HIGH"] for f in findings):
            completeness = COMPLETENESS_REQUIRES_REVIEW
        else:
            completeness = COMPLETENESS_COMPLETE

        # Calculate Evidence Coverage
        total_regulatory_rules = len(RULE_REGISTRY)
        active_regulatory_rules = [r for r in RULE_REGISTRY if r.get("rule_type") != "PENDING_CONFIRMATION"]
        rules_with_findings = {f.rule_code for f in findings if f.rule_code}
        # Evidence coverage is the ratio of evaluated rules supported by evidence
        evidence_coverage_pct = round(
            (len(docs) / max(1, len(active_regulatory_rules))) * 100.0 if docs else 0.0,
            1,
        )
        evidence_coverage_pct = min(100.0, evidence_coverage_pct)

        explanation = (
            f"Risk score of {final_score:.0f}/100 categorized as {risk_band} Risk ({completeness}). "
            f"Evaluated {len(contributing_factors)} contributing factor(s) across {len(docs)} uploaded file(s). "
            f"Score represents deterministic administrative decision support, not an automated approval or rejection verdict."
        )

        factor_breakdown_data = {
            "version": RISK_SCORING_VERSION,
            "weights_used": active_weights,
            "validation_run_id": latest_run.id,
            "contributing_factors": contributing_factors,
            "missing_evidence_items": missing_evidence_items,
            "unresolved_reviews": unresolved_reviews,
            "completeness_status": completeness,
            "is_provisional": completeness != COMPLETENESS_COMPLETE,
            "explanation": explanation,
        }

        # Persist new RiskAssessment record (maintaining historical assessments)
        assessment = RiskAssessment(
            application_id=app.id,
            document_id=None,
            assessment_level="Application",
            score=final_score,
            risk_band=risk_band,
            factor_breakdown=factor_breakdown_data,
            evidence_coverage=evidence_coverage_pct,
            assessment_version=RISK_SCORING_VERSION,
            calculated_at=datetime.utcnow(),
        )
        db.add(assessment)

        # Audit Event
        audit = AuditEvent(
            entity_type="Application",
            entity_id=app.id,
            action="RISK_EVALUATION",
            details={
                "assessment_id": assessment.id,
                "score": final_score,
                "risk_band": risk_band,
                "completeness": completeness,
                "factors_count": len(contributing_factors),
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(assessment)

        return {
            "id": assessment.id,
            "application_id": app.id,
            "application_identifier": app.application_identifier,
            "validation_run_id": latest_run.id,
            "score": final_score,
            "risk_band": risk_band,
            "completeness_status": completeness,
            "evidence_coverage": evidence_coverage_pct,
            "is_provisional": completeness != COMPLETENESS_COMPLETE,
            "explanation": explanation,
            "assessment_version": RISK_SCORING_VERSION,
            "contributing_factors": contributing_factors,
            "missing_evidence_items": missing_evidence_items,
            "unresolved_reviews": unresolved_reviews,
            "calculated_at": assessment.calculated_at,
        }

    @staticmethod
    def get_latest_risk_report(db: Session, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest persisted risk assessment report for an application."""
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.application_id == app.id)
            .order_by(desc(RiskAssessment.calculated_at))
            .first()
        )

        if not assessment:
            return None

        breakdown = assessment.factor_breakdown or {}

        return {
            "id": assessment.id,
            "application_id": app.id,
            "application_identifier": app.application_identifier,
            "validation_run_id": breakdown.get("validation_run_id"),
            "score": assessment.score,
            "risk_band": assessment.risk_band,
            "completeness_status": breakdown.get("completeness_status", "COMPLETE"),
            "evidence_coverage": assessment.evidence_coverage,
            "is_provisional": breakdown.get("is_provisional", False),
            "explanation": breakdown.get("explanation", ""),
            "assessment_version": assessment.assessment_version,
            "contributing_factors": breakdown.get("contributing_factors", []),
            "missing_evidence_items": breakdown.get("missing_evidence_items", []),
            "unresolved_reviews": breakdown.get("unresolved_reviews", []),
            "calculated_at": assessment.calculated_at,
        }

    @staticmethod
    def get_risk_history(db: Session, application_id: str) -> List[Dict[str, Any]]:
        """Retrieves the historical timeline of risk evaluations for an application."""
        assessments = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.application_id == application_id)
            .order_by(desc(RiskAssessment.calculated_at))
            .all()
        )
        history = []
        for a in assessments:
            breakdown = a.factor_breakdown or {}
            history.append({
                "id": a.id,
                "score": a.score,
                "risk_band": a.risk_band,
                "completeness_status": breakdown.get("completeness_status", "COMPLETE"),
                "calculated_at": a.calculated_at,
                "factors_count": len(breakdown.get("contributing_factors", [])),
            })
        return history
