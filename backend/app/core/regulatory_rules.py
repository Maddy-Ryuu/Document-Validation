"""
AICTE Approval Process Handbook (APH 2026-27) Rule Registry
Defines official verified regulatory rules, traceable section citations,
and project-defined technical integrity checks.
"""

from typing import Dict, Any, List

# Rule classifications
TYPE_OFFICIAL_REGULATORY = "OFFICIAL_REGULATORY"
TYPE_TECHNICAL_CHECK = "TECHNICAL_CHECK"
TYPE_PENDING_CONFIRMATION = "PENDING_CONFIRMATION"

RULE_REGISTRY: List[Dict[str, Any]] = [
    {
        "rule_code": "APH-RULE-DOC-CHECKLIST",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "Mandatory Statutory Document Submission",
        "category": "Regulatory",
        "severity": "CRITICAL",
        "description": "Verification that all mandatory statutory documents prescribed in AICTE Approval Process Handbook (APH 2026-27 Chapter II / Annexure 1) are submitted.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II - Grant of Approval through Scrutiny / Re-Scrutiny Committee",
            "page": "Clause 2.4 & Annexure 1 (Mandatory Documents to be uploaded)",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": None,
        "condition": "ALL_MANDATORY_DOCUMENTS_PRESENT",
    },
    {
        "rule_code": "APH-RULE-DOC-EXPIRY",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "Statutory Clearance Validity & Expiry",
        "category": "Safety Compliance",
        "severity": "CRITICAL",
        "description": "Mandatory safety clearances (such as Fire Safety NOC) must possess validity extending into the applicable academic processing cycle.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1, Clause 1.4 - Fire Safety Certificate Norms",
            "page": "Clause 1.4(b) (Valid NOC from Competent State Fire Authority)",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Fire Safety NOC",
        "condition": "EXPIRY_DATE_AFTER_CYCLE_START",
    },
    {
        "rule_code": "APH-RULE-CROSS-ID-MISMATCH",
        "rule_version": "1.0",
        "rule_type": TYPE_TECHNICAL_CHECK,
        "name": "Cross-Document Institutional Identity Matching",
        "category": "Document Discrepancy",
        "severity": "CRITICAL",
        "description": "Technical check ensuring extracted institutional names, college AICTE identifiers, or campus addresses match application master records.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II, Clause 2.4.3 - Document Authenticity & Institutional Ownership",
            "page": "Clause 2.4.3",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": None,
        "condition": "INSTITUTION_NAME_AND_ID_CONSISTENT",
    },
    {
        "rule_code": "APH-RULE-LAND-NORM",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "Minimum Contiguous Land Area Norm",
        "category": "Land Norms",
        "severity": "HIGH",
        "description": "Technical institutions must satisfy the minimum contiguous land area requirement prescribed in Appendix 4 of APH 2026-27 for the respective discipline and location (Mega/Metro/Urban/Rural).",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Appendix 4 - Norms for Land and Built-up Area Requirements",
            "page": "Table 4.1 (Land Requirements for Technical Institutions)",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Land Ownership and Title Certificate",
        "condition": "LAND_AREA_GREATER_THAN_EQUAL_MINIMUM",
        "threshold": 2.5,  # 2.5 Acres minimum in urban / semi-urban
    },
    {
        "rule_code": "APH-RULE-FAC-PRINCIPAL",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "Regular Qualified Principal / Director Requirement",
        "category": "Faculty Ratio",
        "severity": "HIGH",
        "description": "Every approved technical institution must have a regular, eligible Principal / Director appointed as per AICTE Regulations & Pay Scales Notification.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Appendix 7 - Norms for Faculty Requirements and Cadre Ratio",
            "page": "Clause 7.1 & Pay Regulations Gazette Notification",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Faculty Cadre & Roster Undertaking",
        "condition": "REQUIRED_FIELD_PRINCIPAL_PRESENT",
    },
    {
        "rule_code": "APH-RULE-DUP-HASH",
        "rule_version": "1.0",
        "rule_type": TYPE_TECHNICAL_CHECK,
        "name": "Cryptographic Hash Collision & Duplicate Guard",
        "category": "Document Discrepancy",
        "severity": "MEDIUM",
        "description": "System check preventing duplicate binary submissions across distinct regulatory checklist slots.",
        "regulatory_source": {
            "title": "AICTE Digital Scrutiny System Guidelines",
            "section": "IT Security & Document Repository Specifications",
            "page": "Technical Integrity Norm 3.1",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org"
        },
        "target_document_type": None,
        "condition": "NO_DUPLICATE_FILE_HASHES",
    },
    {
        "rule_code": "APH-RULE-PENDING-SATELLITE-GIS",
        "rule_version": "1.0",
        "rule_type": TYPE_PENDING_CONFIRMATION,
        "name": "Satellite / Geo-Tagging Boundary Verification",
        "category": "Infrastructure",
        "severity": "INFO",
        "description": "Verification of contiguous boundary coordinates via National Master Plan (PM Gati Shakti portal). Requirement pending official technical gateway integration.",
        "regulatory_source": {
            "title": "AICTE Draft Circular on Geo-Tagging of Campuses",
            "section": "Draft Infrastructure Verification Matrix",
            "page": "Pending Gazetted Confirmation",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org"
        },
        "target_document_type": None,
        "condition": "REQUIREMENT_PENDING_CONFIRMATION",
    }
]
