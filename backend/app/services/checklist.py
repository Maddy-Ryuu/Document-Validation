from typing import Dict, List, Any


# Configurable document checklist according to AICTE Approval Process Handbook (APH 2026-27)
AICTE_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Land Ownership and Title Certificate",
        "description": "Registered sale deed / gift deed / government lease agreement showing contiguous land in name of applicant Society/Trust",
        "required_for": ["New Institute", "Extension of Approval (EoA)", "Increase in Intake", "Change of Site / Location"],
        "criticality": "Mandatory",
        "target_fields": ["survey_number", "land_area", "land_area_unit", "owner_name", "registration_date"]
    },
    {
        "category": "Land Use Certificate & Non-Encumbrance (NOC)",
        "description": "Certificate from competent revenue authority certifying land use conversion and freedom from encumbrances",
        "required_for": ["New Institute", "Change of Site / Location"],
        "criticality": "Mandatory",
        "target_fields": ["khasra_survey_no", "issuing_authority", "conversion_purpose", "issue_date"]
    },
    {
        "category": "Fire Safety NOC",
        "description": "Valid Fire and Emergency Services NOC issued by Director / Chief Fire Officer of respective State / UT",
        "required_for": ["New Institute", "Extension of Approval (EoA)", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["certificate_number", "issuing_authority", "valid_until", "issue_date", "building_name"]
    },
    {
        "category": "Approved Building Plan & Sanction Order",
        "description": "Building plan sanctioned by Town Planning / Municipal Authority / Competent Authority reflecting built-up instructional area",
        "required_for": ["New Institute", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["sanction_order_number", "built_up_area_sqm", "instructional_area_sqm", "architect_license", "approval_date"]
    },
    {
        "category": "Architect Certificate of Completion & Barrier-Free Access",
        "description": "Certification by registered architect verifying completion of instructional, administrative and amenities spaces as per APH norms",
        "required_for": ["New Institute", "Increase in Intake"],
        "criticality": "Required",
        "target_fields": ["architect_name", "coa_registration_number", "total_carpet_area", "barrier_free_access_verified"]
    },
    {
        "category": "University Affiliation / State Govt Permission",
        "description": "NOC / Affiliation letter issued by the affiliating University and approval letter from State Higher/Technical Education Department",
        "required_for": ["New Institute", "Extension of Approval (EoA)", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["university_name", "order_number", "academic_year", "approved_programmes"]
    },
    {
        "category": "Faculty Cadre & Roster Undertaking",
        "description": "List of core faculty members, qualifications, AICTE faculty IDs, and cadre ratio declaration",
        "required_for": ["Extension of Approval (EoA)", "Increase in Intake"],
        "criticality": "Required",
        "target_fields": ["principal_director_name", "total_faculty_count", "cadre_ratio_declared"]
    },
    {
        "category": "Trust / Society Registration Deed",
        "description": "Certificate of registration under Societies Registration Act, 1860 or Indian Trusts Act, 1882 with Memorandum of Association",
        "required_for": ["New Institute"],
        "criticality": "Mandatory",
        "target_fields": ["trust_society_name", "registration_number", "registration_date"]
    },
    {
        "category": "Other Regulatory Supporting Documents",
        "description": "Pollution Control Board NOC, water safety certificate, or institutional undertakings",
        "required_for": [],
        "criticality": "Optional",
        "target_fields": ["document_title", "issue_date", "issuing_authority"]
    }
]


def get_checklist_for_application(application_category: str, academic_year: str) -> List[Dict[str, Any]]:
    items = []
    for doc in AICTE_DOCUMENT_CHECKLIST:
        is_mandatory = (
            not doc["required_for"] or
            any(req.lower() in application_category.lower() for req in doc["required_for"])
        )
        items.append({
            "category": doc["category"],
            "description": doc["description"],
            "criticality": doc["criticality"] if is_mandatory else "Optional",
            "is_mandatory": is_mandatory,
            "target_fields": doc["target_fields"],
        })
    return items
