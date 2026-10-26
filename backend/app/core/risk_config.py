"""
risk_config.py
Configurable scoring model for AICTE Application Risk Evaluation.
Deterministic weights, factor definitions, and penalty criteria based on compliance findings.
"""

from typing import Dict, Any

RISK_SCORING_VERSION = "APH-2026-27-RISK-v1.0"

# Initial configurable weights (not official AICTE risk weights, configurable for administrative scrutiny)
DEFAULT_RISK_WEIGHTS: Dict[str, int] = {
    "CRITICAL_COMPLIANCE_FAILURE": 30,
    "MAJOR_COMPLIANCE_FAILURE": 20,
    "MINOR_COMPLIANCE_FAILURE": 10,
    "MISSING_REQUIRED_EVIDENCE": 15,
    "UNVERIFIED_DOCUMENT_AUTHENTICITY": 15,
    "CROSS_DOCUMENT_INCONSISTENCIES": 20,
    "EXPIRED_REGULATORY_DOCUMENTS": 20,
    "PROVISIONAL_REVIEW_PENALTY": 10,
}

# Risk category threshold bands
RISK_BANDS = {
    "LOW": {"min": 0, "max": 29, "label": "Low Risk"},
    "MEDIUM": {"min": 30, "max": 59, "label": "Medium Risk"},
    "HIGH": {"min": 60, "max": 100, "label": "High Risk"},
}

# Completeness statuses
COMPLETENESS_COMPLETE = "COMPLETE"
COMPLETENESS_INCOMPLETE = "INCOMPLETE"
COMPLETENESS_REQUIRES_REVIEW = "REQUIRES_REVIEW"
