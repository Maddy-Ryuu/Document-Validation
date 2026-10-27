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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Affidavit 2",
        },
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4 - Processing Fee",
        },
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.3",
        },
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.3(d)",
        },
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.4",
        },
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4 - Satellite Imagery",
        },
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4",
        },
    },
]

# Increase in Intake Dedicated Document Checklist (APH 2026-27 Chapter II & Chapter IV)
INCREASE_INTAKE_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Affidavit 2",
        "description": "Affidavit 2 (Annexure 1): Digital signature by Chairman/Secretary, ₹100 e-stamp, sworn before First Class Judicial Magistrate, Notary, or Oath Commissioner.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Affidavit 2",
        },
    },
    {
        "category": "AICTE Portal Payment Receipt",
        "description": "AICTE Portal Payment Receipt for Increase in Intake processing fee (required if applicable).",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required if application processing fee applies under APH fee structure.",
        "target_fields": [
            "transaction_reference",
            "payment_date",
            "payment_amount",
            "portal_challan_number",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4 - Processing Fee",
        },
    },
    {
        "category": "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "description": "Valid Occupancy Certificate / Completion Certificate / Building Licence / Form D issued by competent authority covering instructional and administrative infrastructure.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.3",
        },
    },
    {
        "category": "Structural Stability Certificate",
        "description": "Structural Stability Certificate issued by a registered structural engineer. Required if building age is more than 30 years from completion certificate date.",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required when the building is more than 30 years old from completion-certificate date.",
        "target_fields": [
            "structural_engineer_name",
            "engineer_registration_number",
            "stability_certified",
            "building_age_years",
            "issue_date",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.3(d)",
        },
    },
    {
        "category": "Fire Safety Certificate",
        "description": "Valid Fire Safety Certificate / NOC issued by competent State Fire authority.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.4",
        },
    },
    {
        "category": "Audited Accounts",
        "description": "Audited financial statements and balance sheet of Trust/Society/Company for previous financial year.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4",
        },
    },
    {
        "category": "University Affiliation / State Govt Permission",
        "description": "NOC / Affiliation approval order from affiliating University and State Higher/Technical Education Department for the proposed intake increase.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "university_name",
            "order_number",
            "academic_year",
            "approved_programmes",
            "proposed_intake",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter IV",
            "clause": "Clause 4.1 - Increase in Intake / Additional Course",
        },
    },
    {
        "category": "Approved Building Plan & Sanction Order",
        "description": "Building plan sanctioned by Town Planning / Municipal Authority reflecting required instructional, administrative and amenities built-up area for expanded intake.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "sanction_order_number",
            "built_up_area_sqm",
            "instructional_area_sqm",
            "architect_license",
            "approval_date",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Appendix 4 & Appendix 5",
            "clause": "Built-up Area Requirements for Increased Intake",
        },
    },
    {
        "category": "Faculty Cadre & Roster Undertaking",
        "description": "Core faculty list, qualifications, AICTE faculty IDs, cadre ratio declaration, and undertaking for appointing required faculty as per student-teacher ratio for additional intake.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "principal_director_name",
            "total_faculty_count",
            "cadre_ratio_declared",
            "student_teacher_ratio",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Appendix 7",
            "clause": "Faculty Cadre Ratio & Cadre Undertaking",
        },
    },
    {
        "category": "Architect Certificate of Completion & Barrier-Free Access",
        "description": "Certification by registered architect verifying instructional readiness, barrier-free access, and safety norms for additional capacity.",
        "criticality": "Required",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "architect_name",
            "coa_registration_number",
            "total_carpet_area",
            "barrier_free_access_verified",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Appendix 5",
            "clause": "Barrier-Free Access & Facilities for Divyangjan",
        },
    },
    {
        "category": "Accreditation Certificate (NBA / NAAC)",
        "description": "Valid NBA / NAAC accreditation certificate for programmes seeking expansion beyond standard slabs, where prescribed by APH norms.",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required for programmes applying for intake increase beyond baseline slabs as per APH norms.",
        "target_fields": [
            "accreditation_agency",
            "accreditation_grade",
            "valid_until",
            "accredited_programmes",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter IV",
            "clause": "Clause 4.1.2 - Accreditation Norms for Expansion",
        },
    },
]

# New Technical Institute Dedicated Document Checklist (APH 2026-27 Chapter I & Annexure 1)
# Exactly the 11 items identified in the reference checklist:
NEW_INSTITUTE_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Approved Building Plan",
        "description": "Approved Building Plan prepared by registered architect / licensed surveyor and approved by competent authority (reflecting instructional, administrative, and amenities area).",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "sanction_order_number",
            "built_up_area_sqm",
            "instructional_area_sqm",
            "architect_license",
            "approval_date",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I & Annexure 1",
            "clause": "Clause 1.3 - Building Plan Approval",
        },
    },
    {
        "category": "Affidavit 2",
        "description": "Affidavit 2 as prescribed in Annexure 1: Digital signature by Chairman/Secretary, ₹100 e-stamp, sworn before First Class Judicial Magistrate, Notary, or Oath Commissioner.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Affidavit 2",
        },
    },
    {
        "category": "Applicant Organisation Resolution (Format 3)",
        "description": "Resolution passed by applicant Trust/Society/Company for establishing new technical institute as prescribed in Format 3.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "resolution_number",
            "resolution_date",
            "trust_society_name",
            "proposed_institute_name",
            "authorized_signatory",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 2",
            "clause": "Format 3 - Resolution of the Applicant Organisation",
        },
    },
    {
        "category": "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "description": "Occupancy Certificate, Completion Certificate, Building Licence or Form D issued by competent authority, or permitted affidavit undertaking where applicable.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I & Annexure 1",
            "clause": "Clause 1.3",
        },
    },
    {
        "category": "Fire Safety Certificate",
        "description": "Valid Fire Safety Certificate / NOC issued by competent State Fire authority.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.4 - Fire Safety Certificate Norms",
        },
    },
    {
        "category": "Bank Manager Certificate 3",
        "description": "Bank Manager Certificate 3 concerning financial status, deposits/funds, and FDR in joint name as per AICTE norms.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "bank_name",
            "branch_name",
            "manager_name",
            "fdr_account_number",
            "deposit_amount",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 2",
            "clause": "Certificate 3 - Bank Manager Certificate",
        },
    },
    {
        "category": "Complete Online Application & Prescribed Hard Copy",
        "description": "Printout of complete submitted online application and receipt/undertaking where required by applicable procedure.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "portal_application_number",
            "submission_date",
            "signature_present",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I",
            "clause": "Clause 1.3 - Submission of Application",
        },
    },
    {
        "category": "Organisation Registration Documents",
        "description": "Registration documents for Trust/Society/Company (Section 8), PPP or BOT structure, including Memorandum of Association, rules, and list of trustees/directors.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "trust_society_name",
            "registration_number",
            "registration_date",
            "registration_act",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I",
            "clause": "Clause 1.2 - Eligible Applicant Bodies",
        },
    },
    {
        "category": "Board of Governors Composition",
        "description": "Board of Governors composition constitution document. Required for standalone PGDM institutions as per APH norms.",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required for standalone PGDM / Management institutions as per APH norms.",
        "target_fields": [
            "chairman_name",
            "total_members",
            "industry_experts_count",
            "academic_experts_count",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I",
            "clause": "Clause 1.5 - Standalone PGDM Norms",
        },
    },
    {
        "category": "Land / Building Ownership Evidence",
        "description": "Registered Sale Deed / Gift Deed / Government Lease Agreement (>= 30 years) showing contiguous land in name of applicant Society/Trust as permitted by APH.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "survey_number",
            "land_area",
            "land_area_unit",
            "owner_name",
            "registration_date",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Appendix 4",
            "clause": "Table 4.1 - Land Requirements for Technical Institutions",
        },
    },
    {
        "category": "Conditional Documents for Section 8 / PPP / BOT Arrangements",
        "description": "Concessionaire Agreement / Government partnership deed / Section 8 non-profit documentation where applicable.",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required for institutions established under Section 8, Public-Private Partnership (PPP), or Build-Operate-Transfer (BOT) models.",
        "target_fields": [
            "agreement_type",
            "partner_authority",
            "agreement_date",
            "validity_tenure_years",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter I",
            "clause": "Clause 1.6 - PPP / BOT / Section 8 Norms",
        },
    },
]

# NRI / Foreign National Quota Dedicated Document Checklist (APH 2026-27 Chapter V)
NRI_FN_QUOTA_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Affidavit 2",
        "description": "Affidavit 2 (Annexure 1): Digital signature by Chairman/Secretary, ₹100 e-stamp, sworn before First Class Judicial Magistrate, Notary, or Oath Commissioner.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Affidavit 2",
        },
    },
    {
        "category": "AICTE Portal Payment Receipt",
        "description": "AICTE Portal Payment Receipt for NRI / Foreign National quota processing fee (required if applicable).",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required if application processing fee applies under APH fee structure.",
        "target_fields": [
            "transaction_reference",
            "payment_date",
            "payment_amount",
            "portal_challan_number",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter V",
            "clause": "Clause 5.1 - Processing Fee",
        },
    },
    {
        "category": "Occupancy Certificate / Completion Certificate / Building Licence / Form D",
        "description": "Valid Occupancy Certificate / Completion Certificate / Building Licence / Form D issued by competent authority.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.3",
        },
    },
    {
        "category": "Fire Safety Certificate",
        "description": "Valid Fire Safety Certificate / NOC issued by competent State Fire authority.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.4",
        },
    },
    {
        "category": "Audited Accounts",
        "description": "Audited financial statements and balance sheet of Trust/Society/Company for previous financial year.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4",
        },
    },
    {
        "category": "Trust / Society Resolution for NRI / FN Quota (Format 3)",
        "description": "Resolution of Trust/Society/Company for introduction or continuation of NRI / Foreign National seats, signed by Chairman/Secretary in Format 3 under Annexure 2 §2.2.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "resolution_number",
            "resolution_date",
            "quota_type",
            "approved_seats_percentage",
            "signatory_designation",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 2",
            "clause": "Annexure 2 Clause 2.2 Format 3",
        },
    },
    {
        "category": "University Affiliation / State Board Approval for Quota Seats",
        "description": "Affiliation letter / NOC from affiliating University and State Higher/Technical Education Department for introduction/continuation of NRI / FN quota seats.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "university_name",
            "order_number",
            "academic_year",
            "quota_seats_approved",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter V",
            "clause": "Clause 5.1 - University Affiliation & State Approval",
        },
    },
    {
        "category": "Accreditation / Eligibility Proof for Supernumerary FN Seats",
        "description": "Valid NBA Accreditation certificate or autonomy proof required specifically for Foreign National / OCI / Gulf Children supernumerary quota (up to 15%).",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required for institutions applying for Foreign National / OCI / Gulf Children supernumerary seats. Conditional if applying strictly for NRI quota (within intake).",
        "target_fields": [
            "accreditation_agency",
            "valid_until",
            "supernumerary_quota_eligible",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter V",
            "clause": "Clause 5.2 - Supernumerary Quota Eligibility",
        },
    },
]

# Change of Site / Location Dedicated Document Checklist (APH 2026-27 Chapter II)
CHANGE_SITE_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Affidavit 2",
        "description": "Affidavit 2 (Annexure 1): Digital signature by Chairman/Secretary, ₹100 e-stamp, sworn before First Class Judicial Magistrate, Notary, or Oath Commissioner.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Affidavit 2",
        },
    },
    {
        "category": "AICTE Portal Payment Receipt",
        "description": "AICTE Portal Payment Receipt for Change of Site / Location processing fee (required if applicable).",
        "criticality": "Conditional",
        "is_mandatory": False,
        "is_conditional": True,
        "condition_description": "Required if application processing fee applies under APH fee structure.",
        "target_fields": [
            "transaction_reference",
            "payment_date",
            "payment_amount",
            "portal_challan_number",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4 - Processing Fee",
        },
    },
    {
        "category": "Audited Accounts",
        "description": "Audited financial statements and balance sheet of Trust/Society/Company for previous financial year.",
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
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.4",
        },
    },
    {
        "category": "Existing Institution Approval & Clearance Record",
        "description": "Copy of previous AICTE Extension of Approval (EoA) and existing approved site records for current campus.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "current_site_address",
            "current_eoa_number",
            "academic_year",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.18 - Change of Site / Location",
        },
    },
    {
        "category": "Affiliating University / Board NOC (Format 2)",
        "description": "No Objection Certificate (NOC) from affiliating University and State Government for change of site/location in prescribed Format 2.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "university_name",
            "noc_number",
            "noc_date",
            "from_location",
            "to_location",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 2",
            "clause": "Format 2 - NOC from Affiliating Body",
        },
    },
    {
        "category": "Applicant Organisation Resolution (Format 3)",
        "description": "Resolution of applicant Trust/Society/Company in Format 3 resolving to shift institute from current site to proposed new site.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "resolution_number",
            "resolution_date",
            "trust_society_name",
            "current_site",
            "proposed_site",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 2",
            "clause": "Format 3 - Resolution of the Applicant Organisation",
        },
    },
    {
        "category": "Land Ownership and Title Certificate (Proposed Site)",
        "description": "Registered sale deed / gift deed / government lease agreement in name of applicant Society/Trust for proposed new location showing contiguous land.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "survey_number",
            "land_area",
            "land_area_unit",
            "owner_name",
            "proposed_site_address",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II & Appendix 4",
            "clause": "Table 4.1 - Land Requirements at Proposed Site",
        },
    },
    {
        "category": "Land Use Certificate & Non-Encumbrance Certificate (Proposed Site)",
        "description": "Certificate from competent revenue authority certifying land use conversion (educational) and freedom from encumbrances for proposed new site.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "khasra_survey_no",
            "issuing_authority",
            "conversion_purpose",
            "issue_date",
            "proposed_site_address",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.18 - Land Conversion & Non-Encumbrance",
        },
    },
    {
        "category": "Approved Building Plan (Proposed Site)",
        "description": "Building plan sanctioned by Town Planning / Municipal Authority for proposed new site reflecting required built-up and instructional area.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "sanction_order_number",
            "built_up_area_sqm",
            "instructional_area_sqm",
            "architect_license",
            "proposed_site_address",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II & Appendix 5",
            "clause": "Building Plan Sanction for Proposed Site",
        },
    },
    {
        "category": "Occupancy Certificate / Completion Certificate (Proposed Site)",
        "description": "Occupancy Certificate / Completion Certificate or Building Licence issued by competent authority for building at proposed new location.",
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
            "proposed_site_address",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Chapter II",
            "clause": "Clause 2.18 - Infrastructure Readiness at New Location",
        },
    },
    {
        "category": "Fire Safety Certificate (Proposed Site)",
        "description": "Valid Fire Safety Certificate / NOC issued by competent Fire authority for building at proposed new location.",
        "criticality": "Mandatory",
        "is_mandatory": True,
        "is_conditional": False,
        "condition_description": None,
        "target_fields": [
            "certificate_number",
            "issuing_authority",
            "valid_until",
            "issue_date",
            "proposed_site_address",
        ],
        "regulatory_source": {
            "title": "AICTE Approval Process Handbook (APH) 2026-27",
            "section": "Annexure 1",
            "clause": "Clause 1.4 - Fire Safety at Proposed Location",
        },
    },
]

# Combined fallback list for backward compatibility with existing tests
AICTE_DOCUMENT_CHECKLIST: List[Dict[str, Any]] = [
    {
        "category": "Land Ownership and Title Certificate",
        "description": "Registered sale deed / gift deed / government lease agreement showing contiguous land in name of applicant Society/Trust",
        "required_for": ["New Institute", "New Technical Institute", "Increase in Intake", "Change of Site / Location"],
        "criticality": "Mandatory",
        "target_fields": ["survey_number", "land_area", "land_area_unit", "owner_name", "registration_date"],
    },
    {
        "category": "Land Use Certificate & Non-Encumbrance (NOC)",
        "description": "Certificate from competent revenue authority certifying land use conversion and freedom from encumbrances",
        "required_for": ["New Institute", "New Technical Institute", "Change of Site / Location"],
        "criticality": "Mandatory",
        "target_fields": ["khasra_survey_no", "issuing_authority", "conversion_purpose", "issue_date"],
    },
    {
        "category": "Fire Safety NOC",
        "description": "Valid Fire and Emergency Services NOC issued by Director / Chief Fire Officer of respective State / UT",
        "required_for": ["New Institute", "New Technical Institute", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["certificate_number", "issuing_authority", "valid_until", "issue_date", "building_name"],
    },
    {
        "category": "Approved Building Plan & Sanction Order",
        "description": "Building plan sanctioned by Town Planning / Municipal Authority / Competent Authority reflecting built-up instructional area",
        "required_for": ["New Institute", "New Technical Institute", "Increase in Intake"],
        "criticality": "Mandatory",
        "target_fields": ["sanction_order_number", "built_up_area_sqm", "instructional_area_sqm", "architect_license", "approval_date"],
    },
    {
        "category": "Architect Certificate of Completion & Barrier-Free Access",
        "description": "Certification by registered architect verifying completion of instructional, administrative and amenities spaces as per APH norms",
        "required_for": ["New Institute", "New Technical Institute", "Increase in Intake"],
        "criticality": "Required",
        "target_fields": ["architect_name", "coa_registration_number", "total_carpet_area", "barrier_free_access_verified"],
    },
    {
        "category": "University Affiliation / State Govt Permission",
        "description": "NOC / Affiliation letter issued by the affiliating University and approval letter from State Higher/Technical Education Department",
        "required_for": ["New Institute", "New Technical Institute", "Increase in Intake"],
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
        "required_for": ["New Institute", "New Technical Institute"],
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


def is_increase_intake_category(application_category: Optional[str]) -> bool:
    """Determine whether an application category represents Increase in Intake."""
    if not application_category:
        return False
    cat = application_category.strip().lower()
    return "increase in intake" in cat or "intake increase" in cat or "additional intake" in cat


def is_new_institute_category(application_category: Optional[str]) -> bool:
    """Determine whether an application category represents New Technical Institute."""
    if not application_category:
        return False
    cat = application_category.strip().lower()
    return (
        "new technical institute" in cat
        or "new institute" in cat
        or "setting up new" in cat
        or cat == "new technical"
    )


def is_nri_fn_category(application_category: Optional[str]) -> bool:
    """Determine whether an application category represents NRI / Foreign National Quota."""
    if not application_category:
        return False
    cat = application_category.strip().lower()
    return (
        "nri" in cat
        or "foreign national" in cat
        or "fn quota" in cat
        or "supernumerary" in cat
        or "gulf" in cat
    )


def is_change_site_category(application_category: Optional[str]) -> bool:
    """Determine whether an application category represents Change of Site / Location."""
    if not application_category:
        return False
    cat = application_category.strip().lower()
    return (
        "change of site" in cat
        or "change of location" in cat
        or "shifting" in cat
        or "site / location" in cat
        or "change site" in cat
    )


def get_checklist_for_application(
    application_category: str, academic_year: str
) -> List[Dict[str, Any]]:
    """
    Returns the document checklist according to AICTE Approval Process Handbook (APH 2026-27).
    - For Extension of Approval (EoA): exactly the 7 reference categories.
    - For Increase in Intake: the 11-category intake expansion checklist.
    - For New Technical Institute: the 11-category institutional establishment checklist.
    - For NRI / Foreign National Quota: the 8-category quota checklist.
    - For Change of Site / Location: the 11-category site-change checklist.
    - Fallback: standard category-specific checklist.
    """
    def copy_checklist(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "category": item["category"],
                "description": item["description"],
                "criticality": item["criticality"],
                "is_mandatory": item["is_mandatory"],
                "is_conditional": item.get("is_conditional", False),
                "condition_description": item.get("condition_description"),
                "target_fields": list(item["target_fields"]),
                "regulatory_source": item.get("regulatory_source"),
            }
            for item in items
        ]

    if is_eoa_category(application_category):
        return copy_checklist(EOA_DOCUMENT_CHECKLIST)

    if is_increase_intake_category(application_category):
        return copy_checklist(INCREASE_INTAKE_DOCUMENT_CHECKLIST)

    if is_new_institute_category(application_category):
        return copy_checklist(NEW_INSTITUTE_DOCUMENT_CHECKLIST)

    if is_nri_fn_category(application_category):
        return copy_checklist(NRI_FN_QUOTA_DOCUMENT_CHECKLIST)

    if is_change_site_category(application_category):
        return copy_checklist(CHANGE_SITE_DOCUMENT_CHECKLIST)

    # Fallback to AICTE_DOCUMENT_CHECKLIST for unrecognized or custom categories
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
            "regulatory_source": None,
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
        "affidavit undertaking",
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
    "Fire Safety NOC": [
        "fire safety noc",
        "fire safety certificate",
        "fire noc",
        "fire certificate",
        "fire clearance",
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
    "Approved Building Plan": [
        "approved building plan",
        "approved building plan & sanction order",
        "building plan",
        "sanctioned building plan",
        "architectural plan",
    ],
    "Approved Building Plan & Sanction Order": [
        "approved building plan & sanction order",
        "approved building plan",
        "building plan",
        "sanction order",
        "sanctioned plan",
    ],
    "Approved Building Plan (Proposed Site)": [
        "approved building plan (proposed site)",
        "approved building plan proposed site",
        "building plan proposed site",
        "proposed site building plan",
        "sanctioned plan proposed site",
    ],
    "Occupancy Certificate / Completion Certificate (Proposed Site)": [
        "occupancy certificate / completion certificate (proposed site)",
        "occupancy certificate proposed site",
        "completion certificate proposed site",
        "building licence proposed site",
        "form d proposed site",
    ],
    "Fire Safety Certificate (Proposed Site)": [
        "fire safety certificate (proposed site)",
        "fire safety noc (proposed site)",
        "fire noc proposed site",
        "fire clearance proposed site",
    ],
    "Applicant Organisation Resolution (Format 3)": [
        "applicant organisation resolution (format 3)",
        "applicant organization resolution (format 3)",
        "format 3 resolution",
        "organisation resolution",
        "organization resolution",
        "format 3",
        "trust resolution",
        "society resolution",
        "board resolution",
    ],
    "Trust / Society Resolution for NRI / FN Quota (Format 3)": [
        "trust / society resolution for nri / fn quota (format 3)",
        "resolution for nri seats",
        "resolution for foreign national quota",
        "format 3 nri quota",
        "nri resolution",
        "format 3 nri",
    ],
    "Affiliating University / Board NOC (Format 2)": [
        "affiliating university / board noc (format 2)",
        "format 2 noc",
        "format 2",
        "university noc for site change",
        "university noc",
        "state board noc",
        "noc from affiliating university",
    ],
    "Bank Manager Certificate 3": [
        "bank manager certificate 3",
        "bank manager certificate",
        "certificate 3",
        "bank certificate 3",
        "bank certificate",
        "fdr certificate",
        "financial status certificate",
    ],
    "Complete Online Application & Prescribed Hard Copy": [
        "complete online application & prescribed hard copy",
        "complete online application",
        "online application printout",
        "prescribed hard copy",
        "submitted online application",
        "aicte portal application copy",
    ],
    "Organisation Registration Documents": [
        "organisation registration documents",
        "organization registration documents",
        "trust registration deed",
        "society registration deed",
        "trust / society registration deed",
        "registration deed",
        "society registration certificate",
        "trust deed",
        "memorandum of association",
    ],
    "Trust / Society Registration Deed": [
        "trust / society registration deed",
        "organisation registration documents",
        "trust registration",
        "society registration deed",
        "society registration",
        "trust deed",
    ],
    "Board of Governors Composition": [
        "board of governors composition",
        "board of governors",
        "bog composition",
        "governing body composition",
        "governing council",
    ],
    "Land / Building Ownership Evidence": [
        "land / building ownership evidence",
        "land ownership and title certificate",
        "land ownership",
        "land deed",
        "registered sale deed",
        "sale deed",
        "lease deed",
        "title certificate",
    ],
    "Land Ownership and Title Certificate": [
        "land ownership and title certificate",
        "land / building ownership evidence",
        "land title certificate",
        "land deed",
        "sale deed",
        "registered land deed",
    ],
    "Land Ownership and Title Certificate (Proposed Site)": [
        "land ownership and title certificate (proposed site)",
        "proposed site land ownership",
        "land deed proposed site",
        "sale deed proposed site",
        "proposed site land deed",
    ],
    "Land Use Certificate & Non-Encumbrance Certificate (Proposed Site)": [
        "land use certificate & non-encumbrance certificate (proposed site)",
        "land use certificate (proposed site)",
        "non-encumbrance certificate (proposed site)",
        "proposed site land use certificate",
        "proposed site land noc",
    ],
    "Land Use Certificate & Non-Encumbrance (NOC)": [
        "land use certificate & non-encumbrance (noc)",
        "land use certificate",
        "non-encumbrance certificate",
        "land noc",
    ],
    "Existing Institution Approval & Clearance Record": [
        "existing institution approval & clearance record",
        "existing approval record",
        "previous eoa copy",
        "previous approval letter",
        "existing site approval",
    ],
    "Conditional Documents for Section 8 / PPP / BOT Arrangements": [
        "conditional documents for section 8 / ppp / bot arrangements",
        "ppp agreement",
        "bot agreement",
        "section 8 documents",
        "concessionaire agreement",
    ],
    "University Affiliation / State Govt Permission": [
        "university affiliation / state govt permission",
        "university affiliation",
        "state govt permission",
        "state government approval order",
        "affiliation order",
    ],
    "University Affiliation / State Board Approval for Quota Seats": [
        "university affiliation / state board approval for quota seats",
        "university affiliation for quota seats",
        "quota affiliation approval",
        "state approval for nri seats",
        "university noc for nri quota",
    ],
    "Accreditation Certificate (NBA / NAAC)": [
        "accreditation certificate (nba / naac)",
        "accreditation certificate",
        "nba accreditation certificate",
        "naac accreditation certificate",
        "nba certificate",
        "naac certificate",
    ],
    "Accreditation / Eligibility Proof for Supernumerary FN Seats": [
        "accreditation / eligibility proof for supernumerary fn seats",
        "nba accreditation for fn seats",
        "supernumerary eligibility proof",
        "autonomy proof for foreign national quota",
        "accreditation certificate (nba / naac)",
    ],
    "Faculty Cadre & Roster Undertaking": [
        "faculty cadre & roster undertaking",
        "faculty cadre",
        "faculty roster",
        "faculty roster undertaking",
        "faculty declaration",
    ],
    "Architect Certificate of Completion & Barrier-Free Access": [
        "architect certificate of completion & barrier-free access",
        "architect certificate",
        "barrier-free access certificate",
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
    if "/" in checklist_category and "(" not in checklist_category:
        subparts = [p.strip().lower() for p in checklist_category.split("/")]
        for p in subparts:
            p_norm = re.sub(r"[^a-z0-9]", "", p)
            if u == p or (len(p_norm) >= 4 and (u_norm == p_norm or p_norm in u_norm or u_norm in p_norm)):
                return True

    return False
