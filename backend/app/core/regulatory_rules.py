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
        "rule_code": "APH-RULE-NEW-INST-TRUST",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "New Institute Applicant Entity Registration & Format 3 Resolution",
        "category": "Governance",
        "severity": "CRITICAL",
        "description": "Establishment of a new technical institution requires certified organization registration documents under eligible Acts (Societies/Trusts/Companies Act Sec 8) and applicant resolution in Format 3.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I & Annexure 2",
            "page": "Clause 1.2 & Annexure 2 Format 3",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Applicant Organisation Resolution (Format 3)",
        "condition": "TRUST_REGISTRATION_AND_FORMAT3_VALID",
    },
    {
        "rule_code": "APH-RULE-NEW-INST-BANK",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "Financial Solvency & Bank Manager Certificate 3",
        "category": "Financial Viability",
        "severity": "HIGH",
        "description": "New institutions must furnish Bank Manager Certificate 3 establishing mandatory fixed deposit receipts (FDR) in joint name and operational financial stability.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 2",
            "page": "Certificate 3 - Certificate of the Bank Manager",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Bank Manager Certificate 3",
        "condition": "BANK_CERTIFICATE_3_VERIFIED",
    },
    {
        "rule_code": "APH-RULE-INTAKE-AFFILIATION",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "University Affiliation & State NOC for Intake Expansion",
        "category": "Academic Approval",
        "severity": "CRITICAL",
        "description": "Applications for Increase in Intake must include valid affiliation orders from the affiliating University and NOC from State Technical Education Department approving additional seats.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter IV - Extension of Approval for Additional Intake / Course",
            "page": "Clause 4.1 & Clause 4.1.1",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "University Affiliation / State Govt Permission",
        "condition": "UNIVERSITY_AFFILIATION_INTAKE_CONFIRMED",
    },
    {
        "rule_code": "APH-RULE-NRI-FN-SUBTYPE",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "NRI / Foreign National Quota Subtype & Supernumerary Verification",
        "category": "Quota Regulatory",
        "severity": "HIGH",
        "description": "Distinguishes NRI Quota (up to 5% within approved intake) from Foreign National / OCI / Gulf Children Supernumerary Quota (up to 15%). Supernumerary seats require valid NBA/autonomy eligibility.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter V - Approval for Children of NRIs / Foreign Nationals / OCI / Gulf",
            "page": "Clause 5.1 & Clause 5.2",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Trust / Society Resolution for NRI / FN Quota (Format 3)",
        "condition": "QUOTA_SUBTYPE_AND_ELIGIBILITY_RESOLVED",
    },
    {
        "rule_code": "APH-RULE-SITE-LOCATION-DISTINCTION",
        "rule_version": "1.0",
        "rule_type": TYPE_OFFICIAL_REGULATORY,
        "name": "Proposed Site Location Verification & Old-Site Reuse Guard",
        "category": "Site Regulatory",
        "severity": "CRITICAL",
        "description": "Applications for Change of Site must submit land ownership, land conversion NOC, approved building plan, and fire clearance specifically pertaining to the proposed new location. Old-site certificates cannot be reused.",
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II - Approval for Change of Site / Location",
            "page": "Clause 2.18 & Annexure 2 Format 2",
            "applicable_academic_year": "2026-2027",
            "source_url": "https://www.aicte-india.org/aphandbook2026-27"
        },
        "target_document_type": "Land Ownership and Title Certificate (Proposed Site)",
        "condition": "PROPOSED_SITE_DOCUMENTS_DISTINCT_FROM_OLD_SITE",
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
