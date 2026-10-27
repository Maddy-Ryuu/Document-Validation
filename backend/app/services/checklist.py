import re
from typing import Dict, List, Any, Optional


# Extension of Approval (EoA) Dedicated Document Checklist according to AICTE Approval Process Handbook (APH 2026-27)
EOA_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Affidavit 2",
        "description": "Digital signature by Chairman/Secretary, ₹100 e-stamp, sworn before a First Class Judicial Magistrate, Notary, or Oath Commissioner.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "affidavit_type",
            "stamp_duty_amount",
            "digital_signature_present",
            "sworn_before",
            "signatory_designation",
        ],
    },
    {
        "category": "AICTE Portal Payment Receipt",
        "description": "AICTE Portal Payment Receipt (required if applicable).",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required if applicable.",
        "target_fields": [
            "transaction_reference",
            "payment_date",
            "payment_amount",
            "portal_challan_number",
        ],
    },
    {
        "category": "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "description": "Must be valid and issued by the competent authority.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "certificate_number",
            "issuing_authority",
            "issue_date",
            "valid_until",
            "building_name",
        ],
    },
    {
        "category": "Structural Stability Certificate",
        "description": "Required when the stated building-age condition applies: the building is more than 30 years old from the completion-certificate date. Must be valid and issued by a registered structural engineer.",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required when the building is more than 30 years old from the completion-certificate date. Must be valid and issued by a registered structural engineer.",
        "target_fields": [
            "structural_engineer_name",
            "engineer_registration_number",
            "stability_certified",
            "building_age_years",
            "issue_date",
        ],
    },
    {
        "category": "Fire Safety Certificate",
        "description": "Must be valid and issued by the competent authority.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "certificate_number",
            "issuing_authority",
            "valid_until",
            "issue_date",
            "building_name",
        ],
    },
    {
        "category": "Satellite Map of Land",
        "description": "Must show the land location and latitude/longitude at the main building entrance.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "latitude",
            "longitude",
            "land_location",
            "entrance_coordinates",
        ],
    },
    {
        "category": "Audited Accounts",
        "description": "Accounts of the Trust/Society/Company for the previous year.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "financial_year",
            "auditor_name",
            "ca_membership_number",
            "balance_sheet_verified",
        ],
    },
]

# Configurable document checklist for non-EoA application types (APH 2026-27)
# Covers: "New Institute", "Increase in Intake", "NRI / Foreign National Quota", "Change of Site / Location"
AICTE_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Land Ownership and Title Certificate",
        "description": "Registered sale deed / gift deed / government lease agreement showing contiguous land in name of applicant Society/Trust",
        "required_for": ["New Institute", "Increase in Intake", "Change of Site / Location"],
        "criticality": "Mandatory",
        "target_fields": ["survey_number", "land_area", "land_area_unit", "owner_name", "registration_date"],
    },
    {
        "category": "Land Use Certificate & Non-Encumbrance (NOC)",
        "description": "Certificate from competent revenue authority certifying land use conversion and freedom from encumbrances",
        "required_for": ["New Institute", "Change of Site / Location"],
        "criticality": "Mandatory",
        "target_fields": ["khasra_survey_no", "issuing_authority", "conversion_purpose", "issue_date"],
    },
    {
        "category": "Fire Safety NOC",
        "description": "Valid Fire and Emergency Services NOC issued by Director / Chief Fire Officer of respective State / UT",
        "required_for": ["New Institute", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["certificate_number", "issuing_authority", "valid_until", "issue_date", "building_name"],
    },
    {
        "category": "Approved Building Plan & Sanction Order",
        "description": "Building plan sanctioned by Town Planning / Municipal Authority / Competent Authority reflecting built-up instructional area",
        "required_for": ["New Institute", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["sanction_order_number", "built_up_area_sqm", "instructional_area_sqm", "architect_license", "approval_date"],
    },
    {
        "category": "Architect Certificate of Completion & Barrier-Free Access",
        "description": "Certification by registered architect verifying completion of instructional, administrative and amenities spaces as per APH norms",
        "required_for": ["New Institute", "Increase in Intake"],
        "criticality": "Required",
        "target_fields": ["architect_name", "coa_registration_number", "total_carpet_area", "barrier_free_access_verified"],
    },
    {
        "category": "University Affiliation / State Govt Permission",
        "description": "NOC / Affiliation letter issued by the affiliating University and approval letter from State Higher/Technical Education Department",
        "required_for": ["New Institute", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["university_name", "order_number", "academic_year", "approved_programmes"],
    },
    {
        "category": "Faculty Cadre & Roster Undertaking",
        "description": "List of core faculty members, qualifications, AICTE faculty IDs, and cadre ratio declaration",
        "required_for": ["Increase in Intake"],
        "criticality": "Required",
        "target_fields": ["principal_director_name", "total_faculty_count", "cadre_ratio_declared"],
    },
    {
        "category": "Trust / Society Registration Deed",
        "description": "Certificate of registration under Societies Registration Act, 1860 or Indian Trusts Act, 1882 with Memorandum of Association",
        "required_for": ["New Institute"],
        "criticality": "Mandatory",
        "target_fields": ["trust_society_name", "registration_number", "registration_date"],
    },
    {
        "category": "Other Regulatory Supporting Documents",
        "description": "Pollution Control Board NOC, water safety certificate, or institutional undertakings",
        "required_for": [],
        "criticality": "Optional",
        "target_fields": ["document_title", "issue_date", "issuing_authority"],
    },
]


def is_eoa_category(application_category: Optional[str]) -> bool:
    """Determine whether an application category represents Extension of Approval (EoA)."""
    if not application_category:
        return False
    cat = application_category.strip().lower()
    return (
        "extension of approval" in cat
        or cat == "eoa"
        or "(eoa)" in cat
        or "eoa" in cat.split()
    )


def get_checklist_for_application(
    application_category: str, academic_year: str
) -> List[Dict[str, Any]]:
    """
    Returns the document checklist according to AICTE Approval Process Handbook (APH 2026-27).
    - For Extension of Approval (EoA): exactly the 7 reference categories.
    - For non-EoA applications (New Institute, Increase in Intake, NRI Quota, Change of Site):
      the standard category-specific checklist.
    """
    if is_eoa_category(application_category):
        return [
            {
                "category": item["category"],
                "description": item["description"],
                "criticality": item["criticality"],
                "is_mandatory": item["is_mandatory"],
                "is_conditional": item.get("is_conditional", False),
                "condition_description": item.get("condition_description"),
                "target_fields": list(item["target_fields"]),
            }
            for item in EOA_DOCUMENT_CHECKLIST
        ]

    # Non-EoA categories
    items = []
    for doc in AICTE_DOCUMENT_CHECKLIST:
        is_mandatory = (
            not doc["required_for"]
            or any(req.lower() in application_category.lower() for req in doc["required_for"])
        )
        items.append({
            "category": doc["category"],
            "description": doc["description"],
            "criticality": doc["criticality"] if is_mandatory else "Optional",
            "is_mandatory": is_mandatory,
            "is_conditional": False,
            "condition_description": None,
            "target_fields": list(doc["target_fields"]),
        })
    return items


# Document Category Aliases for backward compatibility and fuzzy matching
CATEGORY_ALIASES: Dict[str, List[str]] = {
    "Affidavit 2": [
        "affidavit 2",
        "affidavit-2",
        "affidavit ii",
        "affidavit 02",
        "affidavit",
        "affidavit - 2",
    ],
    "AICTE Portal Payment Receipt": [
        "aicte portal payment receipt",
        "portal payment receipt",
        "payment receipt",
        "aicte payment receipt",
        "challan receipt",
        "fee receipt",
        "portal challan",
    ],
    "Occupancy Certificate / Completion Certificate / Building Licence / Form D": [
        "occupancy certificate / completion certificate / building licence / form d",
        "occupancy certificate",
        "completion certificate",
        "building licence",
        "building license",
        "form d",
        "occupancy / completion certificate",
        "occupancy certificate / completion certificate",
        "approved building plan & sanction order",
        "architect certificate of completion & barrier-free access",
    ],
    "Structural Stability Certificate": [
        "structural stability certificate",
        "structural stability",
        "building stability certificate",
        "stability certificate",
        "structural certificate",
    ],
    "Fire Safety Certificate": [
        "fire safety certificate",
        "fire safety noc",
        "no objection certificate (fire safety noc)",
        "fire noc",
        "fire certificate",
        "fire clearance",
        "fire safety",
    ],
    "Satellite Map of Land": [
        "satellite map of land",
        "satellite map",
        "satellite map & geo coordinates",
        "land satellite map",
        "gis map",
        "satellite imagery",
    ],
    "Audited Accounts": [
        "audited accounts",
        "audited balance sheet",
        "audited financial statements",
        "audited statement of accounts",
        "annual audited accounts",
        "audited accounts of trust/society/company",
        "balance sheet",
    ],
    "Land Ownership and Title Certificate": [
        "land ownership and title certificate",
        "land title certificate",
        "land deed",
        "sale deed",
        "registered land deed",
    ],
    "Land Use Certificate & Non-Encumbrance (NOC)": [
        "land use certificate & non-encumbrance (noc)",
        "land use certificate",
        "non-encumbrance certificate",
        "land noc",
    ],
    "Approved Building Plan & Sanction Order": [
        "approved building plan & sanction order",
        "building plan",
        "sanction order",
    ],
    "Architect Certificate of Completion & Barrier-Free Access": [
        "architect certificate of completion & barrier-free access",
        "architect certificate",
    ],
    "University Affiliation / State Govt Permission": [
        "university affiliation / state govt permission",
        "university affiliation",
        "state govt permission",
        "state government approval order",
    ],
    "Faculty Cadre & Roster Undertaking": [
        "faculty cadre & roster undertaking",
        "faculty cadre",
        "faculty roster",
        "faculty roster undertaking",
    ],
    "Trust / Society Registration Deed": [
        "trust / society registration deed",
        "trust registration",
        "society registration deed",
        "society registration",
    ],
    "Other Regulatory Supporting Documents": [
        "other regulatory supporting documents",
        "supporting documents",
        "other documents",
    ],
}


def is_document_match(uploaded_doc_type: str, checklist_category: str) -> bool:
    """
    Robust comparison between an uploaded document type and a checklist category.
    Handles exact case-insensitive matches, normalized strings, slashes, and known aliases.
    """
    if not uploaded_doc_type or not checklist_category:
        return False

    u = uploaded_doc_type.strip().lower()
    c = checklist_category.strip().lower()

    if u == c:
        return True

    # Normalized comparison (alphanumeric only)
    u_norm = re.sub(r"[^a-z0-9]", "", u)
    c_norm = re.sub(r"[^a-z0-9]", "", c)
    if u_norm == c_norm and len(u_norm) > 0:
        return True

    # Check forward aliases for target checklist category
    aliases = CATEGORY_ALIASES.get(checklist_category, [])
    for alias in aliases:
        a_norm = re.sub(r"[^a-z0-9]", "", alias.lower())
        if u == alias.lower() or u_norm == a_norm:
            return True
        if len(alias) >= 5 and (alias.lower() in u or u in alias.lower()):
            return True

    # Check reverse aliases if uploaded_doc_type is registered
    rev_aliases = CATEGORY_ALIASES.get(uploaded_doc_type, [])
    for alias in rev_aliases:
        a_norm = re.sub(r"[^a-z0-9]", "", alias.lower())
        if c == alias.lower() or c_norm == a_norm:
            return True
        if len(alias) >= 5 and (alias.lower() in c or c in alias.lower()):
            return True

    # Check multi-name slash separated categories
    if "/" in checklist_category:
        subparts = [p.strip().lower() for p in checklist_category.split("/")]
        for p in subparts:
            p_norm = re.sub(r"[^a-z0-9]", "", p)
            if u == p or (len(p_norm) >= 4 and (u_norm == p_norm or p_norm in u_norm or u_norm in p_norm)):
                return True

    return False
