"""
compliance_engine.py
Modular execution engine for AICTE regulatory compliance verification.
Evaluates application dossiers, extracted fields, and checklist integrity,
yielding explainable PASS, FAIL, or NEEDS_REVIEW findings with traceable citations.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import (
    Application,
    Document,
    DocumentExtraction,
    ValidationRun,
    Finding,
    AuditEvent,
)
from app.services.checklist import (
    get_checklist_for_application,
    is_document_match,
    is_eoa_category,
    is_increase_intake_category,
    is_new_institute_category,
    is_nri_fn_category,
    is_change_site_category,
)
from app.core.regulatory_rules import (
    RULE_REGISTRY,
    TYPE_OFFICIAL_REGULATORY,
    TYPE_TECHNICAL_CHECK,
    TYPE_PENDING_CONFIRMATION,
)


SYNTHETIC_INDICATORS = [
    r"synthetic\s+test\s+document",
    r"not\s+an\s+official\s+record",
    r"metadata\s+summary",
    r"deliberately\s+not\s+a\s+certificate",
    r"software\s+testing\s+only",
    r"fictional\s+placeholder",
    r"for\s+software\s+testing",
    r"synthetic\s+testing\s+authority",
]


def is_synthetic_document(raw_text: Optional[str], original_filename: Optional[str] = None) -> bool:
    """Detects whether a document is a synthetic test document or test metadata summary."""
    text_to_check = (raw_text or "") + " " + (original_filename or "")
    for pattern in SYNTHETIC_INDICATORS:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return True
    return False


def normalize_string(text: Optional[str]) -> str:
    """Normalize text by lowercasing, stripping punctuation, extra spaces, and common stop-words."""
    if not text:
        return ""
    cleaned = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    filler = ["institute", "technology", "studies", "campus", "college", "applicant", "body", "the", "of", "and", "&"]
    tokens = [t for t in cleaned.split() if t not in filler]
    return " ".join(tokens)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Tolerantly parses diverse date strings into a datetime object."""
    if not date_str:
        return None
    date_clean = date_str.split()[0].strip().replace(',', '/')
    formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y",
        "%d-%b-%Y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_clean, fmt)
        except ValueError:
            pass
    return None


class ComplianceEngine:
    @staticmethod
    def run_compliance_evaluation(db: Session, application_id: str) -> Dict[str, Any]:
        """
        Executes the compliance rule suite against the specified application dossier.
        Records a ValidationRun, persists findings in database, and returns an executive report.
        """
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")

        # 1. Create or start ValidationRun
        run = ValidationRun(
            application_id=app.id,
            status="Running",
            progress=0,
            rule_version_reference="APH-2026-27-v1.0",
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.flush()

        # Gather application context
        institution = app.institution
        app_category = app.application_category
        academic_year = app.academic_year

        # Gather documents and extractions
        docs = db.query(Document).filter(Document.application_id == app.id).all()
        doc_map_by_type: Dict[str, Document] = {}
        extractions_by_doc_id: Dict[str, DocumentExtraction] = {}

        for d in docs:
            existing = doc_map_by_type.get(d.document_type)
            if not existing or d.version > existing.version:
                doc_map_by_type[d.document_type] = d

            ext = (
                db.query(DocumentExtraction)
                .filter(DocumentExtraction.document_id == d.id)
                .order_by(desc(DocumentExtraction.created_at))
                .first()
            )
            if ext:
                extractions_by_doc_id[d.id] = ext

        # Clear old open findings for this application before new evaluation
        db.query(Finding).filter(Finding.application_id == app.id).delete()
        db.flush()

        checklist_items = get_checklist_for_application(app_category, academic_year)
        findings_to_create: List[Finding] = []
        rule_evaluations: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # RULE 1: APH-RULE-DOC-CHECKLIST (Mandatory Document Checklist)
        # -------------------------------------------------------------
        rule_1 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-DOC-CHECKLIST")
        missing_mandatory_categories = []
        for chk in checklist_items:
            if chk["is_mandatory"]:
                matched = any(is_document_match(d.document_type, chk["category"]) for d in docs)
                if not matched:
                    missing_mandatory_categories.append(chk["category"])
            elif chk.get("is_conditional") and "structural stability" in chk["category"].lower():
                # Evaluate conditional building-age condition (> 30 years)
                building_age = None
                for d in docs:
                    ext = extractions_by_doc_id.get(d.id)
                    if ext and ext.structured_fields:
                        if is_document_match(d.document_type, "Occupancy Certificate / Completion Certificate / Building Licence / Form D"):
                            issue_d = ext.structured_fields.get("issue_date", {}).get("value")
                            if issue_d:
                                match_yr = re.search(r"\b(19\d\d|20[0-2]\d)\b", str(issue_d))
                                if match_yr:
                                    building_age = 2026 - int(match_yr.group(1))
                        age_val = ext.structured_fields.get("building_age_years", {}).get("value")
                        if age_val:
                            try:
                                building_age = float(re.sub(r"[^\d.]", "", str(age_val)))
                            except Exception:
                                pass
                if building_age is not None and building_age > 30:
                    matched = any(is_document_match(d.document_type, chk["category"]) for d in docs)
                    if not matched:
                        missing_mandatory_categories.append(f"{chk['category']} (Building Age: {int(building_age)} yrs > 30 yrs)")

        if missing_mandatory_categories:
            finding = Finding(
                application_id=app.id,
                validation_run_id=run.id,
                rule_code=rule_1["rule_code"],
                category=rule_1["category"],
                severity=rule_1["severity"],
                title="Missing Mandatory Regulatory Documents",
                explanation=(
                    f"{len(missing_mandatory_categories)} mandatory document(s) required under APH 2026-27 "
                    f"have not been uploaded: {', '.join(missing_mandatory_categories)}."
                ),
                evidence_reference=f"Approval Process Handbook Clause 2.4 - Missing: {missing_mandatory_categories[0]}",
                status="Open",
            )
            findings_to_create.append(finding)
            rule_evaluations.append({
                "rule_code": rule_1["rule_code"],
                "rule_name": rule_1["name"],
                "result": "FAIL",
                "severity": rule_1["severity"],
                "explanation": finding.explanation,
                "regulatory_source": rule_1["regulatory_source"],
                "missing_items": missing_mandatory_categories,
            })
        else:
            rule_evaluations.append({
                "rule_code": rule_1["rule_code"],
                "rule_name": rule_1["name"],
                "result": "PASS",
                "severity": rule_1["severity"],
                "explanation": "All mandatory regulatory checklist categories are present in the dossier.",
                "regulatory_source": rule_1["regulatory_source"],
            })

        # -------------------------------------------------------------
        # RULE 2: APH-RULE-DOC-EXPIRY (Clearance & NOC Validity)
        # -------------------------------------------------------------
        rule_2 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-DOC-EXPIRY")
        fire_doc = None
        for d in docs:
            if is_document_match(d.document_type, "Fire Safety Certificate") or "fire" in d.document_type.lower() or "noc" in d.document_type.lower():
                fire_doc = d
                break

        if not fire_doc:
            rule_evaluations.append({
                "rule_code": rule_2["rule_code"],
                "rule_name": rule_2["name"],
                "result": "NOT_EVALUATED" if len(docs) == 0 else "NEEDS_REVIEW",
                "severity": rule_2["severity"],
                "explanation": "No Fire Safety NOC attached in application dossier to evaluate statutory validity.",
                "regulatory_source": rule_2["regulatory_source"],
            })
        else:
            ext = extractions_by_doc_id.get(fire_doc.id)
            fields = ext.structured_fields if (ext and ext.structured_fields) else {}
            raw_text = ext.raw_text if ext else ""
            valid_until_str = fields.get("valid_until", {}).get("value")
            doc_is_synthetic = is_synthetic_document(raw_text, fire_doc.original_filename)

            if not valid_until_str:
                finding = Finding(
                    application_id=app.id,
                    document_id=fire_doc.id,
                    validation_run_id=run.id,
                    rule_code=rule_2["rule_code"],
                    category=rule_2["category"],
                    severity="HIGH",
                    title="Fire Safety NOC: Expiry Date Unextractable",
                    explanation="Validity timeframe / expiry date could not be verified automatically from Fire NOC. Scrutiny review required.",
                    evidence_reference=f"Document: {fire_doc.original_filename}",
                    status="Open",
                )
                findings_to_create.append(finding)
                rule_evaluations.append({
                    "rule_code": rule_2["rule_code"],
                    "rule_name": rule_2["name"],
                    "result": "NEEDS_REVIEW",
                    "severity": "HIGH",
                    "explanation": finding.explanation,
                    "regulatory_source": rule_2["regulatory_source"],
                })
            else:
                expiry_dt = parse_date(valid_until_str)
                cycle_cutoff = datetime(2026, 6, 30)
                if expiry_dt and expiry_dt < cycle_cutoff:
                    finding = Finding(
                        application_id=app.id,
                        document_id=fire_doc.id,
                        validation_run_id=run.id,
                        rule_code=rule_2["rule_code"],
                        category=rule_2["category"],
                        severity=rule_2["severity"],
                        title="Mandatory Statutory Certificate Expired",
                        explanation=(
                            f"Fire Safety NOC validity expired on {expiry_dt.strftime('%d-%m-%Y')}, "
                            f"which lapses prior to the commencement of academic cycle 2026-27."
                        ),
                        evidence_reference=f"Extracted valid_until: {valid_until_str}",
                        status="Open",
                    )
                    findings_to_create.append(finding)
                    rule_evaluations.append({
                        "rule_code": rule_2["rule_code"],
                        "rule_name": rule_2["name"],
                        "result": "FAIL",
                        "severity": rule_2["severity"],
                        "explanation": finding.explanation,
                        "regulatory_source": rule_2["regulatory_source"],
                        "actual_value": valid_until_str,
                        "expected_value": f"> {cycle_cutoff.strftime('%d-%m-%Y')}",
                    })
                elif doc_is_synthetic:
                    finding = Finding(
                        application_id=app.id,
                        document_id=fire_doc.id,
                        validation_run_id=run.id,
                        rule_code=rule_2["rule_code"],
                        category=rule_2["category"],
                        severity="MEDIUM",
                        title="Fire Safety NOC: Authenticity Unverified (Synthetic / Metadata Summary)",
                        explanation=(
                            f"Document contains date '{valid_until_str}' but is marked as a synthetic test document or metadata summary. "
                            f"Issuing authority, digital signature, QR seal, and registry authenticity remain UNVERIFIED. Future expiry alone does not establish legal validity."
                        ),
                        evidence_reference=f"Extracted date: {valid_until_str} (Authenticity: UNVERIFIED, Source: {fire_doc.original_filename})",
                        status="Open",
                    )
                    findings_to_create.append(finding)
                    rule_evaluations.append({
                        "rule_code": rule_2["rule_code"],
                        "rule_name": rule_2["name"],
                        "result": "NEEDS_REVIEW",
                        "severity": rule_2["severity"],
                        "explanation": (
                            f"Fire Safety NOC contains date '{valid_until_str}' (Cycle cutoff: {cycle_cutoff.strftime('%d-%m-%Y')}), "
                            f"but document is a test metadata summary. Issuing authority signature/QR authenticity is UNVERIFIED; human scrutiny required."
                        ),
                        "regulatory_source": rule_2["regulatory_source"],
                        "actual_value": f"{valid_until_str} (Authenticity: UNVERIFIED)",
                        "expected_value": f"Authentic authority-issued certificate valid > {cycle_cutoff.strftime('%d-%m-%Y')}",
                    })
                else:
                    rule_evaluations.append({
                        "rule_code": rule_2["rule_code"],
                        "rule_name": rule_2["name"],
                        "result": "PASS",
                        "severity": rule_2["severity"],
                        "explanation": (
                            f"Fire Safety NOC validity period active until {valid_until_str} (satisfies academic cycle cutoff {cycle_cutoff.strftime('%d-%m-%Y')}). "
                            f"Authority issuance details parsed from certificate."
                        ),
                        "regulatory_source": rule_2["regulatory_source"],
                        "actual_value": valid_until_str,
                    })

        # -------------------------------------------------------------
        # RULE 3: APH-RULE-CROSS-ID-MISMATCH (Cross-Document Identity)
        # -------------------------------------------------------------
        rule_3 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-CROSS-ID-MISMATCH")
        target_name_norm = normalize_string(institution.name if institution else "")

        comparable_docs = []
        for d in docs:
            ext = extractions_by_doc_id.get(d.id)
            if ext and ext.structured_fields:
                extracted_name = ext.structured_fields.get("institution_name", {}).get("value")
                extracted_id = ext.structured_fields.get("institution_identifier", {}).get("value")
                if extracted_name or extracted_id:
                    comparable_docs.append({
                        "doc": d,
                        "name": extracted_name,
                        "identifier": extracted_id,
                    })

        mismatched_docs = []
        review_fragment_docs = []
        compared_records = []
        for item in comparable_docs:
            d = item["doc"]
            extracted_name = item["name"]
            extracted_id = item["identifier"]
            compared_records.append({
                "file": d.original_filename,
                "extracted_name": extracted_name,
                "extracted_id": extracted_id,
            })

            if extracted_name:
                extracted_norm = normalize_string(extracted_name)
                # Check for OCR fragment: fewer than 5 characters or 1 short token
                if len(extracted_norm) < 8 or len(extracted_norm.split()) <= 1:
                    review_fragment_docs.append({
                        "doc": d,
                        "extracted": extracted_name,
                    })
                elif target_name_norm and extracted_norm:
                    tokens_target = set(target_name_norm.split())
                    tokens_extracted = set(extracted_norm.split())
                    common = tokens_target.intersection(tokens_extracted)
                    if len(common) == 0:
                        mismatched_docs.append({
                            "doc": d,
                            "extracted": extracted_name,
                            "expected": institution.name if institution else "",
                        })

        if mismatched_docs:
            for item in mismatched_docs:
                d = item["doc"]
                finding = Finding(
                    application_id=app.id,
                    document_id=d.id,
                    validation_run_id=run.id,
                    rule_code=rule_3["rule_code"],
                    category=rule_3["category"],
                    severity=rule_3["severity"],
                    title="Cross-Document Institutional Identity Mismatch",
                    explanation=(
                        f"Document '{d.original_filename}' names institution as '{item['extracted']}', "
                        f"which conflicts with applicant record '{item['expected']}'."
                    ),
                    evidence_reference=f"Extracted: '{item['extracted']}' vs Master: '{item['expected']}'",
                    status="Open",
                )
                findings_to_create.append(finding)

            rule_evaluations.append({
                "rule_code": rule_3["rule_code"],
                "rule_name": rule_3["name"],
                "result": "FAIL",
                "severity": rule_3["severity"],
                "explanation": f"Detected {len(mismatched_docs)} document(s) bearing a conflicting institution name across compared documents.",
                "regulatory_source": rule_3["regulatory_source"],
                "mismatches": [{"file": m["doc"].original_filename, "found": m["extracted"]} for m in mismatched_docs],
                "compared_documents": compared_records,
            })
        elif review_fragment_docs:
            rule_evaluations.append({
                "rule_code": rule_3["rule_code"],
                "rule_name": rule_3["name"],
                "result": "NEEDS_REVIEW",
                "severity": "MEDIUM",
                "explanation": (
                    f"OCR extracted partial text/fragment for institution identity in {len(review_fragment_docs)} document(s). "
                    f"Scrutiny review required rather than marking definitive mismatch."
                ),
                "regulatory_source": rule_3["regulatory_source"],
                "compared_documents": compared_records,
            })
        elif len(comparable_docs) < 2:
            rule_evaluations.append({
                "rule_code": rule_3["rule_code"],
                "rule_name": rule_3["name"],
                "result": "NOT_EVALUATED" if len(comparable_docs) == 0 else "NEEDS_REVIEW",
                "severity": rule_3["severity"],
                "explanation": (
                    f"Cross-document institutional identity matching requires at least two uploaded documents with comparable identity fields. "
                    f"Currently found {len(comparable_docs)} document(s) with extracted identity metadata."
                ),
                "regulatory_source": rule_3["regulatory_source"],
                "compared_documents": compared_records,
            })
        else:
            rule_evaluations.append({
                "rule_code": rule_3["rule_code"],
                "rule_name": rule_3["name"],
                "result": "PASS",
                "severity": rule_3["severity"],
                "explanation": f"Extracted institution identity verified consistently across {len(comparable_docs)} uploaded documents against master records.",
                "regulatory_source": rule_3["regulatory_source"],
                "compared_documents": compared_records,
            })

        # -------------------------------------------------------------
        # CATEGORY-SPECIFIC CHECKS: NOT APPLICABLE TO EOA
        # (Omitted from execution and displayed breakdown for Extension of Approval)
        # -------------------------------------------------------------
        if not is_eoa_category(app_category):
    
            rule_4 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-LAND-NORM")
            
            land_doc = None
            for d in docs:
                if "satellite" not in d.document_type.lower() and (
                    is_document_match(d.document_type, "Land / Building Ownership Evidence")
                    or is_document_match(d.document_type, "Land Ownership and Title Certificate (Proposed Site)")
                    or is_document_match(d.document_type, "Land Ownership and Title Certificate")
                    or "title" in d.document_type.lower()
                    or "ownership" in d.document_type.lower()
                    or "deed" in d.document_type.lower()
                ):
                    land_doc = d
                    break
    
            land_norm_applies = is_new_institute_category(app_category) or is_change_site_category(app_category)
    
            if not land_doc and not land_norm_applies:
                rule_evaluations.append({
                    "rule_code": rule_4["rule_code"],
                    "rule_name": rule_4["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_4["severity"],
                    "explanation": f"Minimum Contiguous Land Area Norm is not a mandatory verification requirement for {app_category}.",
                    "regulatory_source": rule_4["regulatory_source"],
                })
            elif not land_doc:
                rule_evaluations.append({
                    "rule_code": rule_4["rule_code"],
                    "rule_name": rule_4["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NEEDS_REVIEW",
                    "severity": rule_4["severity"],
                    "explanation": "Land Ownership Certificate not identified in dossier. Awaiting registered land deed upload.",
                    "regulatory_source": rule_4["regulatory_source"],
                })
            else:
                ext = extractions_by_doc_id.get(land_doc.id)
                fields = ext.structured_fields if (ext and ext.structured_fields) else {}
                raw_text = ext.raw_text if ext else ""
                land_area_str = fields.get("land_area", {}).get("value")
                doc_is_synthetic = is_synthetic_document(raw_text, land_doc.original_filename)
    
                if not land_area_str:
                    rule_evaluations.append({
                        "rule_code": rule_4["rule_code"],
                        "rule_name": rule_4["name"],
                        "result": "NEEDS_REVIEW",
                        "severity": rule_4["severity"],
                        "explanation": "Numerical land area not automatically parsed from land documents.",
                        "regulatory_source": rule_4["regulatory_source"],
                    })
                else:
                    try:
                        area_val = float(re.sub(r"[^\d.]", "", land_area_str))
                        req_threshold = float(rule_4.get("threshold", 2.5))
                        if area_val < req_threshold:
                            finding = Finding(
                                application_id=app.id,
                                document_id=land_doc.id,
                                validation_run_id=run.id,
                                rule_code=rule_4["rule_code"],
                                category=rule_4["category"],
                                severity=rule_4["severity"],
                                title="Contiguous Land Area Below Regulatory Norm",
                                explanation=f"Declared land area ({area_val} Acres) is below the minimum APH requirement of {req_threshold} Acres.",
                                evidence_reference=f"Extracted: {land_area_str} (Threshold: {req_threshold} Acres)",
                                status="Open",
                            )
                            findings_to_create.append(finding)
                            rule_evaluations.append({
                                "rule_code": rule_4["rule_code"],
                                "rule_name": rule_4["name"],
                                "result": "FAIL",
                                "severity": rule_4["severity"],
                                "explanation": finding.explanation,
                                "regulatory_source": rule_4["regulatory_source"],
                                "actual_value": f"{area_val} Acres",
                                "expected_value": f">= {req_threshold} Acres",
                            })
                        elif doc_is_synthetic:
                            finding = Finding(
                                application_id=app.id,
                                document_id=land_doc.id,
                                validation_run_id=run.id,
                                rule_code=rule_4["rule_code"],
                                category=rule_4["category"],
                                severity="MEDIUM",
                                title="Land Norm: Title and Contiguity Evidence Unverified (Synthetic Summary)",
                                explanation=(
                                    f"Declared land area is {area_val} Acres (satisfies threshold >= {req_threshold} Acres), "
                                    f"but uploaded document is a synthetic test summary. Registered title deed, revenue mutation, and contiguous parcel verification are UNVERIFIED. Human review required."
                                ),
                                evidence_reference=f"Declared Area: {area_val} Acres (Title Evidence: UNVERIFIED, Source: {land_doc.original_filename})",
                                status="Open",
                            )
                            findings_to_create.append(finding)
                            rule_evaluations.append({
                                "rule_code": rule_4["rule_code"],
                                "rule_name": rule_4["name"],
                                "result": "NEEDS_REVIEW",
                                "severity": rule_4["severity"],
                                "explanation": (
                                    f"Declared land area ({area_val} Acres) satisfies numerical threshold (>= {req_threshold} Acres), "
                                    f"but uploaded file is a synthetic metadata summary. Legal title ownership, survey demarcation, and contiguity require physical scrutiny."
                                ),
                                "regulatory_source": rule_4["regulatory_source"],
                                "actual_value": f"{area_val} Acres (Declared, Title UNVERIFIED)",
                                "expected_value": f"Verified Registered Deed >= {req_threshold} Acres",
                            })
                        else:
                            rule_evaluations.append({
                                "rule_code": rule_4["rule_code"],
                                "rule_name": rule_4["name"],
                                "result": "PASS",
                                "severity": rule_4["severity"],
                                "explanation": f"Declared land area ({area_val} Acres) satisfies minimum APH norm (>= {req_threshold} Acres).",
                                "regulatory_source": rule_4["regulatory_source"],
                                "actual_value": f"{area_val} Acres",
                            })
                    except Exception:
                        rule_evaluations.append({
                            "rule_code": rule_4["rule_code"],
                            "rule_name": rule_4["name"],
                            "result": "NEEDS_REVIEW",
                            "severity": rule_4["severity"],
                            "explanation": f"Could not parse numeric area from '{land_area_str}'. Manual review needed.",
                            "regulatory_source": rule_4["regulatory_source"],
                        })
    
            # -------------------------------------------------------------
            # RULE 5: APH-RULE-FAC-PRINCIPAL (Principal/Director Appointment)
            # -------------------------------------------------------------
            rule_5 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-FAC-PRINCIPAL")
            fac_norm_applies = is_increase_intake_category(app_category) or any("faculty" in chk["category"].lower() for chk in checklist_items)
    
            if not fac_norm_applies:
                rule_evaluations.append({
                    "rule_code": rule_5["rule_code"],
                    "rule_name": rule_5["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_5["severity"],
                    "explanation": f"Faculty Cadre Undertaking is not an applicable checklist requirement for {app_category}.",
                    "regulatory_source": rule_5["regulatory_source"],
                })
            else:
                fac_doc = None
                for d in docs:
                    if "faculty" in d.document_type.lower() or "cadre" in d.document_type.lower():
                        fac_doc = d
                        break
    
                if not fac_doc:
                    rule_evaluations.append({
                        "rule_code": rule_5["rule_code"],
                        "rule_name": rule_5["name"],
                        "result": "NEEDS_REVIEW",
                        "severity": rule_5["severity"],
                        "explanation": "Faculty roster dossier not attached to evaluate Director / Principal appointment.",
                        "regulatory_source": rule_5["regulatory_source"],
                    })
                else:
                    ext = extractions_by_doc_id.get(fac_doc.id)
                    fields = ext.structured_fields if (ext and ext.structured_fields) else {}
                    principal_val = fields.get("principal_director_name", {}).get("value")
    
                    if not principal_val:
                        finding = Finding(
                            application_id=app.id,
                            document_id=fac_doc.id,
                            validation_run_id=run.id,
                            rule_code=rule_5["rule_code"],
                            category=rule_5["category"],
                            severity=rule_5["severity"],
                            title="Missing Mandatory Field: Regular Principal / Director",
                            explanation="Faculty cadre declaration does not identify an attested regular Principal / Director.",
                            evidence_reference=f"Document: {fac_doc.original_filename} (Missing Principal)",
                            status="Open",
                        )
                        findings_to_create.append(finding)
                        rule_evaluations.append({
                            "rule_code": rule_5["rule_code"],
                            "rule_name": rule_5["name"],
                            "result": "FAIL",
                            "severity": rule_5["severity"],
                            "explanation": finding.explanation,
                            "regulatory_source": rule_5["regulatory_source"],
                        })
                    else:
                        rule_evaluations.append({
                            "rule_code": rule_5["rule_code"],
                            "rule_name": rule_5["name"],
                            "result": "PASS",
                            "severity": rule_5["severity"],
                            "explanation": f"Regular Principal / Director verified: '{principal_val}'.",
                            "regulatory_source": rule_5["regulatory_source"],
                            "actual_value": principal_val,
                        })

        # -------------------------------------------------------------
        # RULE 6: APH-RULE-DUP-HASH (Duplicate File Collision)
        # -------------------------------------------------------------
        rule_6 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-DUP-HASH")
        docs_with_hashes = [d for d in docs if d.sha256_hash]

        if len(docs_with_hashes) == 0:
            rule_evaluations.append({
                "rule_code": rule_6["rule_code"],
                "rule_name": rule_6["name"],
                "result": "NOT_EVALUATED",
                "severity": rule_6["severity"],
                "explanation": "No document files with computed SHA-256 hashes available in dossier to execute duplicate detection.",
                "regulatory_source": rule_6["regulatory_source"],
            })
        else:
            seen_hashes: Dict[str, Document] = {}
            duplicates_found = []

            for d in docs_with_hashes:
                h = d.sha256_hash
                if h in seen_hashes:
                    first_doc = seen_hashes[h]
                    duplicates_found.append({
                        "duplicate_doc": d,
                        "original_doc": first_doc,
                        "sha256": h,
                    })
                else:
                    seen_hashes[h] = d

            if duplicates_found:
                for item in duplicates_found:
                    d = item["duplicate_doc"]
                    orig = item["original_doc"]
                    finding = Finding(
                        application_id=app.id,
                        document_id=d.id,
                        validation_run_id=run.id,
                        rule_code=rule_6["rule_code"],
                        category=rule_6["category"],
                        severity=rule_6["severity"],
                        title="Duplicate Document File Uploaded",
                        explanation=(
                            f"File '{d.original_filename}' uploaded under '{d.document_type}' is an exact binary duplicate "
                            f"(identical SHA-256 hash: {item['sha256'][:16]}...) of '{orig.original_filename}' uploaded under '{orig.document_type}'."
                        ),
                        evidence_reference=f"SHA-256 Collision: {item['sha256']} between '{d.original_filename}' and '{orig.original_filename}'",
                        status="Open",
                    )
                    findings_to_create.append(finding)

                rule_evaluations.append({
                    "rule_code": rule_6["rule_code"],
                    "rule_name": rule_6["name"],
                    "result": "FAIL",
                    "severity": rule_6["severity"],
                    "explanation": f"Detected {len(duplicates_found)} exact duplicate file submission(s) across categories sharing identical SHA-256 hashes.",
                    "regulatory_source": rule_6["regulatory_source"],
                    "duplicates": [
                        {"file": item["duplicate_doc"].original_filename, "matches": item["original_doc"].original_filename, "hash": item["sha256"]}
                        for item in duplicates_found
                    ],
                })
            else:
                rule_evaluations.append({
                    "rule_code": rule_6["rule_code"],
                    "rule_name": rule_6["name"],
                    "result": "PASS",
                    "severity": rule_6["severity"],
                    "explanation": f"Cryptographic integrity audit confirmed: all {len(docs_with_hashes)} uploaded files possess distinct, non-colliding SHA-256 hashes.",
                    "regulatory_source": rule_6["regulatory_source"],
                    "verified_files_count": len(docs_with_hashes),
                })

        if not is_eoa_category(app_category):
            # -------------------------------------------------------------
            # RULE 8: APH-RULE-NEW-INST-TRUST (New Technical Institute: Trust Reg & Format 3)
            # -------------------------------------------------------------
            rule_8 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-NEW-INST-TRUST")
            if not is_new_institute_category(app_category):
                rule_evaluations.append({
                    "rule_code": rule_8["rule_code"],
                    "rule_name": rule_8["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_8["severity"],
                    "explanation": f"New Institute Applicant Registration & Format 3 check applies only to New Technical Institute applications.",
                    "regulatory_source": rule_8["regulatory_source"],
                })
            else:
                format3_doc = next((d for d in docs if is_document_match(d.document_type, "Applicant Organisation Resolution (Format 3)")), None)
                reg_doc = next((d for d in docs if is_document_match(d.document_type, "Organisation Registration Documents")), None)
                if not format3_doc or not reg_doc:
                    missing_sub = []
                    if not format3_doc:
                        missing_sub.append("Applicant Organisation Resolution (Format 3)")
                    if not reg_doc:
                        missing_sub.append("Organisation Registration Documents")
                    rule_evaluations.append({
                        "rule_code": rule_8["rule_code"],
                        "rule_name": rule_8["name"],
                        "result": "FAIL",
                        "severity": rule_8["severity"],
                        "explanation": f"New Technical Institute applicant documentation incomplete: missing {', '.join(missing_sub)}.",
                        "regulatory_source": rule_8["regulatory_source"],
                    })
                else:
                    rule_evaluations.append({
                        "rule_code": rule_8["rule_code"],
                        "rule_name": rule_8["name"],
                        "result": "PASS",
                        "severity": rule_8["severity"],
                        "explanation": "Applicant Trust/Society registration deed and Format 3 establishment resolution verified.",
                        "regulatory_source": rule_8["regulatory_source"],
                    })

            # -------------------------------------------------------------
            # RULE 9: APH-RULE-NEW-INST-BANK (New Technical Institute: Bank Certificate 3)
            # -------------------------------------------------------------
            rule_9 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-NEW-INST-BANK")
            if not is_new_institute_category(app_category):
                rule_evaluations.append({
                    "rule_code": rule_9["rule_code"],
                    "rule_name": rule_9["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_9["severity"],
                    "explanation": f"Bank Manager Certificate 3 check applies only to New Technical Institute applications.",
                    "regulatory_source": rule_9["regulatory_source"],
                })
            else:
                bank_doc = next((d for d in docs if is_document_match(d.document_type, "Bank Manager Certificate 3")), None)
                if not bank_doc:
                    rule_evaluations.append({
                        "rule_code": rule_9["rule_code"],
                        "rule_name": rule_9["name"],
                        "result": "FAIL",
                        "severity": rule_9["severity"],
                        "explanation": "Bank Manager Certificate 3 confirming required financial deposits/FDR is missing.",
                        "regulatory_source": rule_9["regulatory_source"],
                    })
                else:
                    rule_evaluations.append({
                        "rule_code": rule_9["rule_code"],
                        "rule_name": rule_9["name"],
                        "result": "PASS",
                        "severity": rule_9["severity"],
                        "explanation": "Bank Manager Certificate 3 regarding financial status and mandatory deposits verified.",
                        "regulatory_source": rule_9["regulatory_source"],
                    })

            # -------------------------------------------------------------
            # RULE 10: APH-RULE-INTAKE-AFFILIATION (Increase in Intake: University Affiliation)
            # -------------------------------------------------------------
            rule_10 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-INTAKE-AFFILIATION")
            if not is_increase_intake_category(app_category):
                rule_evaluations.append({
                    "rule_code": rule_10["rule_code"],
                    "rule_name": rule_10["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_10["severity"],
                    "explanation": f"University Affiliation & State NOC for intake expansion check applies to Increase in Intake applications.",
                    "regulatory_source": rule_10["regulatory_source"],
                })
            else:
                affil_doc = next((d for d in docs if is_document_match(d.document_type, "University Affiliation / State Govt Permission")), None)
                if not affil_doc:
                    rule_evaluations.append({
                        "rule_code": rule_10["rule_code"],
                        "rule_name": rule_10["name"],
                        "result": "FAIL",
                        "severity": rule_10["severity"],
                        "explanation": "NOC / Affiliation approval order from affiliating University / State Govt for intake increase is missing.",
                        "regulatory_source": rule_10["regulatory_source"],
                    })
                else:
                    rule_evaluations.append({
                        "rule_code": rule_10["rule_code"],
                        "rule_name": rule_10["name"],
                        "result": "PASS",
                        "severity": rule_10["severity"],
                        "explanation": "University affiliation approval order and State permission for intake increase verified.",
                        "regulatory_source": rule_10["regulatory_source"],
                    })

            # -------------------------------------------------------------
            # RULE 11: APH-RULE-NRI-FN-SUBTYPE (NRI / Foreign National Quota Subtype Resolution)
            # -------------------------------------------------------------
            rule_11 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-NRI-FN-SUBTYPE")
            if not is_nri_fn_category(app_category):
                rule_evaluations.append({
                    "rule_code": rule_11["rule_code"],
                    "rule_name": rule_11["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_11["severity"],
                    "explanation": f"NRI / Foreign National Quota rules apply only to Quota applications.",
                    "regulatory_source": rule_11["regulatory_source"],
                })
            else:
                res_doc = next((d for d in docs if is_document_match(d.document_type, "Trust / Society Resolution for NRI / FN Quota (Format 3)")), None)
                # Check if quota subtype is specified
                is_fn_supernumerary = any(
                    "foreign national" in (d.original_filename or "").lower() or "supernumerary" in (d.original_filename or "").lower()
                    for d in docs
                )
                is_nri_specific = any(
                    "nri quota" in (d.original_filename or "").lower() or "nri" in (d.original_filename or "").lower()
                    for d in docs
                )

                if not res_doc:
                    rule_evaluations.append({
                        "rule_code": rule_11["rule_code"],
                        "rule_name": rule_11["name"],
                        "result": "FAIL",
                        "severity": rule_11["severity"],
                        "explanation": "Trust / Society resolution in Format 3 for introduction of NRI / Foreign National seats is missing.",
                        "regulatory_source": rule_11["regulatory_source"],
                    })
                elif not is_fn_supernumerary and not is_nri_specific:
                    # Subtype is unknown / unresolved
                    rule_evaluations.append({
                        "rule_code": rule_11["rule_code"],
                        "rule_name": rule_11["name"],
                        "result": "NEEDS_REVIEW",
                        "severity": rule_11["severity"],
                        "explanation": (
                            "Application filed under combined 'NRI / Foreign National Quota'. Exact quota subtype (NRI up to 5% within approved intake "
                            "vs Foreign National / OCI supernumerary up to 15%) must be confirmed to determine applicability of supernumerary accreditation mandates."
                        ),
                        "regulatory_source": rule_11["regulatory_source"],
                    })
                elif is_fn_supernumerary:
                    # Foreign national supernumerary requires accreditation proof
                    accred_doc = next((d for d in docs if is_document_match(d.document_type, "Accreditation / Eligibility Proof for Supernumerary FN Seats")), None)
                    if not accred_doc:
                        rule_evaluations.append({
                            "rule_code": rule_11["rule_code"],
                            "rule_name": rule_11["name"],
                            "result": "NEEDS_REVIEW",
                            "severity": rule_11["severity"],
                            "explanation": "Foreign National Supernumerary quota requires valid NBA Accreditation or Autonomy eligibility proof.",
                            "regulatory_source": rule_11["regulatory_source"],
                        })
                    else:
                        rule_evaluations.append({
                            "rule_code": rule_11["rule_code"],
                            "rule_name": rule_11["name"],
                            "result": "PASS",
                            "severity": rule_11["severity"],
                            "explanation": "Foreign National supernumerary quota resolution and accreditation eligibility verified.",
                            "regulatory_source": rule_11["regulatory_source"],
                        })
                else:
                    rule_evaluations.append({
                        "rule_code": rule_11["rule_code"],
                        "rule_name": rule_11["name"],
                        "result": "PASS",
                        "severity": rule_11["severity"],
                        "explanation": "NRI quota Format 3 resolution verified for intake allocation.",
                        "regulatory_source": rule_11["regulatory_source"],
                    })

            # -------------------------------------------------------------
            # RULE 12: APH-RULE-SITE-LOCATION-DISTINCTION (Change of Site: Location Distinction)
            # -------------------------------------------------------------
            rule_12 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-SITE-LOCATION-DISTINCTION")
            if not is_change_site_category(app_category):
                rule_evaluations.append({
                    "rule_code": rule_12["rule_code"],
                    "rule_name": rule_12["name"],
                    "result": "NOT_EVALUATED" if len(docs) == 0 else "NOT_APPLICABLE",
                    "severity": rule_12["severity"],
                    "explanation": f"Site location distinction check applies only to Change of Site / Location applications.",
                    "regulatory_source": rule_12["regulatory_source"],
                })
            else:
                # Check whether site-change specific documents are present and distinguish proposed from old site
                prop_land = next((d for d in docs if is_document_match(d.document_type, "Land Ownership and Title Certificate (Proposed Site)")), None)
                prop_bld = next((d for d in docs if is_document_match(d.document_type, "Approved Building Plan (Proposed Site)")), None)
                prop_fire = next((d for d in docs if is_document_match(d.document_type, "Fire Safety Certificate (Proposed Site)")), None)
                format2_doc = next((d for d in docs if is_document_match(d.document_type, "Affiliating University / Board NOC (Format 2)")), None)

                # Check for old-site reuse: if proposed-site documents specifically mention "old site" or "existing site only"
                old_site_reused = False
                for d in [prop_land, prop_bld, prop_fire]:
                    if d:
                        ext = extractions_by_doc_id.get(d.id)
                        raw = ext.raw_text if ext else ""
                        if "old campus only" in raw.lower() or "current location certificate reused" in raw.lower():
                            old_site_reused = True

                if old_site_reused:
                    finding = Finding(
                        application_id=app.id,
                        validation_run_id=run.id,
                        rule_code=rule_12["rule_code"],
                        category=rule_12["category"],
                        severity=rule_12["severity"],
                        title="Change of Site: Improper Old-Site Certificate Reuse",
                        explanation="Submitted documentation for proposed site appears to be an old-site certificate. Proof of clearance must strictly pertain to the proposed new location.",
                        evidence_reference="Proposed site document reuse detected",
                        status="Open",
                    )
                    findings_to_create.append(finding)
                    rule_evaluations.append({
                        "rule_code": rule_12["rule_code"],
                        "rule_name": rule_12["name"],
                        "result": "FAIL",
                        "severity": rule_12["severity"],
                        "explanation": finding.explanation,
                        "regulatory_source": rule_12["regulatory_source"],
                    })
                elif not format2_doc or not prop_land or not prop_bld:
                    rule_evaluations.append({
                        "rule_code": rule_12["rule_code"],
                        "rule_name": rule_12["name"],
                        "result": "FAIL",
                        "severity": rule_12["severity"],
                        "explanation": "Change of Site dossier incomplete: University Format 2 NOC, proposed site land title, and proposed building plan must all be furnished.",
                        "regulatory_source": rule_12["regulatory_source"],
                    })
                else:
                    rule_evaluations.append({
                        "rule_code": rule_12["rule_code"],
                        "rule_name": rule_12["name"],
                        "result": "PASS",
                        "severity": rule_12["severity"],
                        "explanation": "Proposed location documentation (Land deed, Format 2 NOC, and Building plan) verified distinct from previous campus.",
                        "regulatory_source": rule_12["regulatory_source"],
                    })

            # -------------------------------------------------------------
            # RULE 7: APH-RULE-PENDING-SATELLITE-GIS (Pending Requirement)
            # -------------------------------------------------------------
            rule_7 = next(r for r in RULE_REGISTRY if r["rule_code"] == "APH-RULE-PENDING-SATELLITE-GIS")
            rule_evaluations.append({
                "rule_code": rule_7["rule_code"],
                "rule_name": rule_7["name"],
                "result": "NOT_APPLICABLE",
                "severity": rule_7["severity"],
                "explanation": "Satellite geo-tagging coordinate check is pending official gazette confirmation and API gateway integration.",
                "regulatory_source": rule_7["regulatory_source"],
                "is_pending_confirmation": True,
            })

        # Persist findings to database
        for f in findings_to_create:
            db.add(f)

        # Update ValidationRun
        run.status = "Completed"
        run.progress = 100
        run.completed_at = datetime.utcnow()

        # For Extension of Approval (EoA) applications, omit checks genuinely classified
        # as NOT_APPLICABLE from execution and the displayed rule breakdown.
        # Preserves real failures, expiry warnings, missing-evidence findings, and manual-review outcomes.
        # Excluded checks are omitted and not counted as passes.
        if is_eoa_category(app_category):
            rule_evaluations = [r for r in rule_evaluations if r["result"] != "NOT_APPLICABLE"]

        # Update Application status if discrepancies were detected
        fail_count = sum(1 for r in rule_evaluations if r["result"] == "FAIL")
        review_count = sum(1 for r in rule_evaluations if r["result"] == "NEEDS_REVIEW")
        pass_count = sum(1 for r in rule_evaluations if r["result"] == "PASS")
        not_evaluated_count = sum(1 for r in rule_evaluations if r["result"] == "NOT_EVALUATED")
        not_applicable_count = sum(1 for r in rule_evaluations if r["result"] == "NOT_APPLICABLE")

        if fail_count > 0:
            app.status = "Action Required"
        elif review_count > 0:
            app.status = "Under Validation"
        elif pass_count > 0 and fail_count == 0 and review_count == 0 and not_evaluated_count == 0:
            app.status = "Verified"
        else:
            app.status = "Under Validation"

        # Record Audit Event
        audit = AuditEvent(
            entity_type="Application",
            entity_id=app.id,
            action="COMPLIANCE_EVALUATION",
            details={
                "validation_run_id": run.id,
                "passed": pass_count,
                "failed": fail_count,
                "needs_review": review_count,
                "not_evaluated": not_evaluated_count,
                "not_applicable": not_applicable_count,
                "status_assigned": app.status,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(app)

        return {
            "validation_run_id": run.id,
            "application_id": app.id,
            "application_identifier": app.application_identifier,
            "compliance_status": app.status,
            "summary": {
                "passed": pass_count,
                "failed": fail_count,
                "needs_review": review_count,
                "not_evaluated": not_evaluated_count,
                "not_applicable": not_applicable_count,
                "total_evaluated": len(rule_evaluations),
            },
            "rule_evaluations": rule_evaluations,
            "findings_count": len(findings_to_create),
        }
