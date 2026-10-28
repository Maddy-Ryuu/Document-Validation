"""
Phase 2: Authoritative Reference Data Service for AICTE Application Validation.
Provides official institution reference records, approved programmes, sanctioned intake,
approval continuity auditing, explainable cross-verification, and source provenance tracking.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.models import (
    Application,
    Institution,
    Document,
    DocumentExtraction,
    Finding,
    AuditEvent,
    InstitutionReferenceRecord,
    ApprovedProgrammeReference,
    InstitutionApprovalHistory,
    normalize_institution_field,
)

logger = logging.getLogger("reference_data_service")

OFFICIAL_SOURCE = "AICTE Central Regulatory Registry (APH 2024-2027)"
DEMO_SOURCE = "Synthetic Demonstration Benchmark (AICTE Approval Process Handbook Reference Data)"
DEMO_DOC_REF = "DEMO-SYNTHETIC-FIXTURE-NOT-OFFICIAL"


class ReferenceDataService:
    @staticmethod
    def seed_authoritative_benchmarks(db: Session) -> int:
        """
        Populates synthetic demonstration benchmark records for the three reference tables.
        Maintains distinct provenance, sanctioned intakes, accreditation statuses,
        and continuous approval histories.
        
        Strict Safety Invariants:
        1. Every demonstration institution and child record is labeled explicitly as synthetic.
        2. is_official is set to False; verification_status is set to 'SYNTHETIC_BENCHMARK'.
        3. Synthetic benchmarks never produce an official-verification outcome.
        4. Fully idempotent: Checks by aicte_permanent_id before inserting; never duplicates records.
        5. Touches only the three reference tables; preserves all existing application and audit data.
        """
        now = datetime.utcnow()
        freshness_date = datetime(2026, 3, 31, 0, 0, 0)

        # -------------------------------------------------------------------
        # Benchmark 1: Premier Engineering Institute (Full approvals, continuous EoA)
        # -------------------------------------------------------------------
        b1_id = "AICTE-INST-001"
        if not db.query(InstitutionReferenceRecord).filter(
            func.upper(InstitutionReferenceRecord.aicte_permanent_id) == b1_id
        ).first():
            ref1 = InstitutionReferenceRecord(
                aicte_permanent_id=b1_id,
                legal_name="Delhi Institute of Technology & Advanced Sciences",
                institution_type="Engineering",
                state="Delhi",
                district_or_city="New Delhi",
                address="Plot 12, Institutional Area, Sector 4, Dwarka, New Delhi 110078",
                standing_status="Approved",
                established_year=2008,
                initial_approval_year=2009,
                latest_approval_year=2025,
                verification_status="SYNTHETIC_BENCHMARK",
                source_provenance=DEMO_SOURCE,
                source_document_ref=DEMO_DOC_REF,
                data_freshness_date=freshness_date,
                is_official=False,
            )
            db.add(ref1)
            db.flush()

            p1_1 = ApprovedProgrammeReference(
                institution_reference_id=ref1.id,
                programme_name="Engineering and Technology",
                course_name="Computer Science and Engineering",
                level="UG",
                approved_intake=180,
                nri_quota_approved=False,
                pio_fn_quota_approved=False,
                accreditation_status="NBA Accredited",
                accreditation_valid_until=datetime(2028, 6, 30),
                academic_year="2025-2026",
                is_active=True,
            )
            p1_2 = ApprovedProgrammeReference(
                institution_reference_id=ref1.id,
                programme_name="Engineering and Technology",
                course_name="Electronics and Communication Engineering",
                level="UG",
                approved_intake=120,
                nri_quota_approved=False,
                pio_fn_quota_approved=False,
                accreditation_status="NBA Accredited",
                accreditation_valid_until=datetime(2027, 6, 30),
                academic_year="2025-2026",
                is_active=True,
            )
            db.add_all([p1_1, p1_2])

            for yr, intake, app_num in [
                ("2023-2024", 300, "AICTE/NRC/1-100234561/2023/EOA-DEMO"),
                ("2024-2025", 300, "AICTE/NRC/1-100234561/2024/EOA-DEMO"),
                ("2025-2026", 300, "AICTE/NRC/1-100234561/2025/EOA-DEMO"),
            ]:
                h = InstitutionApprovalHistory(
                    institution_reference_id=ref1.id,
                    academic_year=yr,
                    eoa_application_number=app_num,
                    eoa_issue_date=datetime(int(yr.split("-")[0]), 5, 20),
                    effective_start_date=datetime(int(yr.split("-")[0]), 7, 1),
                    effective_end_date=datetime(int(yr.split("-")[1]), 6, 30),
                    total_sanctioned_intake=intake,
                    approval_type="Extension of Approval",
                    issuing_authority="Member Secretary, AICTE New Delhi",
                    is_latest=(yr == "2025-2026"),
                )
                db.add(h)

        # -------------------------------------------------------------------
        # Benchmark 2: Research Institute with Approved NRI Quota
        # -------------------------------------------------------------------
        b2_id = "AICTE-INST-002"
        if not db.query(InstitutionReferenceRecord).filter(
            func.upper(InstitutionReferenceRecord.aicte_permanent_id) == b2_id
        ).first():
            ref2 = InstitutionReferenceRecord(
                aicte_permanent_id=b2_id,
                legal_name="Maharashtra Institute of Technology & Research",
                institution_type="Engineering",
                state="Maharashtra",
                district_or_city="Pune",
                address="Paud Road, Kothrud, Pune, Maharashtra 411038",
                standing_status="Approved",
                established_year=2001,
                initial_approval_year=2002,
                latest_approval_year=2025,
                verification_status="SYNTHETIC_BENCHMARK",
                source_provenance=DEMO_SOURCE,
                source_document_ref=DEMO_DOC_REF,
                data_freshness_date=freshness_date,
                is_official=False,
            )
            db.add(ref2)
            db.flush()

            p2_1 = ApprovedProgrammeReference(
                institution_reference_id=ref2.id,
                programme_name="Engineering and Technology",
                course_name="Mechanical Engineering",
                level="UG",
                approved_intake=120,
                nri_quota_approved=True,
                nri_quota_intake=18,
                pio_fn_quota_approved=True,
                pio_fn_quota_intake=18,
                accreditation_status="NAAC A+",
                accreditation_valid_until=datetime(2029, 12, 31),
                academic_year="2025-2026",
                is_active=True,
            )
            p2_2 = ApprovedProgrammeReference(
                institution_reference_id=ref2.id,
                programme_name="Engineering and Technology",
                course_name="Artificial Intelligence and Data Science",
                level="UG",
                approved_intake=60,
                nri_quota_approved=True,
                nri_quota_intake=9,
                pio_fn_quota_approved=False,
                pio_fn_quota_intake=0,
                accreditation_status="Non-Accredited",
                academic_year="2025-2026",
                is_active=True,
            )
            db.add_all([p2_1, p2_2])

            for yr, intake, app_num in [
                ("2024-2025", 180, "AICTE/WRO/1-100876122/2024/EOA-DEMO"),
                ("2025-2026", 180, "AICTE/WRO/1-100876122/2025/EOA-DEMO"),
            ]:
                h = InstitutionApprovalHistory(
                    institution_reference_id=ref2.id,
                    academic_year=yr,
                    eoa_application_number=app_num,
                    eoa_issue_date=datetime(int(yr.split("-")[0]), 5, 15),
                    effective_start_date=datetime(int(yr.split("-")[0]), 7, 1),
                    effective_end_date=datetime(int(yr.split("-")[1]), 6, 30),
                    total_sanctioned_intake=intake,
                    approval_type="Extension of Approval",
                    issuing_authority="Regional Officer, AICTE WRO Mumbai",
                    is_latest=(yr == "2025-2026"),
                )
                db.add(h)

        # -------------------------------------------------------------------
        # Benchmark 3: Management Institute
        # -------------------------------------------------------------------
        b3_id = "AICTE-INST-003"
        if not db.query(InstitutionReferenceRecord).filter(
            func.upper(InstitutionReferenceRecord.aicte_permanent_id) == b3_id
        ).first():
            ref3 = InstitutionReferenceRecord(
                aicte_permanent_id=b3_id,
                legal_name="Karnataka Global School of Management",
                institution_type="Management",
                state="Karnataka",
                district_or_city="Bengaluru",
                address="Electronic City Phase 1, Hosur Road, Bengaluru 560100",
                standing_status="Approved",
                established_year=2014,
                initial_approval_year=2015,
                latest_approval_year=2025,
                verification_status="SYNTHETIC_BENCHMARK",
                source_provenance=DEMO_SOURCE,
                source_document_ref=DEMO_DOC_REF,
                data_freshness_date=freshness_date,
                is_official=False,
            )
            db.add(ref3)
            db.flush()

            p3_1 = ApprovedProgrammeReference(
                institution_reference_id=ref3.id,
                programme_name="Management",
                course_name="Master of Business Administration (MBA)",
                level="PG",
                approved_intake=120,
                nri_quota_approved=False,
                pio_fn_quota_approved=False,
                accreditation_status="NBA Accredited",
                accreditation_valid_until=datetime(2027, 6, 30),
                academic_year="2025-2026",
                is_active=True,
            )
            db.add(p3_1)

            h3 = InstitutionApprovalHistory(
                institution_reference_id=ref3.id,
                academic_year="2025-2026",
                eoa_application_number="AICTE/SWRO/1-209983411/2025/EOA-DEMO",
                eoa_issue_date=datetime(2025, 6, 1),
                effective_start_date=datetime(2025, 7, 1),
                effective_end_date=datetime(2026, 6, 30),
                total_sanctioned_intake=120,
                approval_type="Extension of Approval",
                issuing_authority="Regional Officer, AICTE SWRO",
                is_latest=True,
            )
            db.add(h3)

        # -------------------------------------------------------------------
        # Benchmark 4: Outdated Approval Institute (Gap detected, last approval 2023-2024)
        # -------------------------------------------------------------------
        b4_id = "AICTE-INST-OUTDATED"
        if not db.query(InstitutionReferenceRecord).filter(
            func.upper(InstitutionReferenceRecord.aicte_permanent_id) == b4_id
        ).first():
            ref4 = InstitutionReferenceRecord(
                aicte_permanent_id=b4_id,
                legal_name="Heritage Polytechnic and Vocational College",
                institution_type="Polytechnic",
                state="Uttar Pradesh",
                district_or_city="Lucknow",
                address="Vikas Nagar, Ring Road, Lucknow 226022",
                standing_status="Approved",
                established_year=2005,
                initial_approval_year=2006,
                latest_approval_year=2023,
                verification_status="SYNTHETIC_BENCHMARK",
                source_provenance=DEMO_SOURCE,
                source_document_ref=DEMO_DOC_REF,
                data_freshness_date=datetime(2024, 3, 31),
                is_official=False,
            )
            db.add(ref4)
            db.flush()

            h4 = InstitutionApprovalHistory(
                institution_reference_id=ref4.id,
                academic_year="2023-2024",
                eoa_application_number="AICTE/NRC/1-443322110/2023/EOA-DEMO",
                eoa_issue_date=datetime(2023, 6, 10),
                effective_start_date=datetime(2023, 7, 1),
                effective_end_date=datetime(2024, 6, 30),
                total_sanctioned_intake=60,
                approval_type="Extension of Approval",
                issuing_authority="Member Secretary, AICTE",
                is_latest=True,
            )
            db.add(h4)

        # -------------------------------------------------------------------
        # Benchmark 5: Disciplinary Action Institute (Adverse Standing)
        # -------------------------------------------------------------------
        b5_id = "AICTE-INST-DEFICIENT"
        if not db.query(InstitutionReferenceRecord).filter(
            func.upper(InstitutionReferenceRecord.aicte_permanent_id) == b5_id
        ).first():
            ref5 = InstitutionReferenceRecord(
                aicte_permanent_id=b5_id,
                legal_name="Apex Global Academy of Technology",
                institution_type="Engineering",
                state="Tamil Nadu",
                district_or_city="Chennai",
                address="Old Mahabalipuram Road, Chennai 600119",
                standing_status="Under Scrutiny",
                established_year=2010,
                initial_approval_year=2011,
                latest_approval_year=2024,
                verification_status="SYNTHETIC_BENCHMARK",
                source_provenance=DEMO_SOURCE,
                source_document_ref=DEMO_DOC_REF,
                data_freshness_date=datetime(2025, 3, 31),
                is_official=False,
            )
            db.add(ref5)
            db.flush()

        db.commit()
        return db.query(InstitutionReferenceRecord).count()

    @classmethod
    def find_reference_record(
        cls,
        db: Session,
        identifier: Optional[str] = None,
        name: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Optional[InstitutionReferenceRecord]:
        """
        Resolves official reference record. Prioritizes exact permanent identifier lookup,
        falling back to normalized name + city + state composite matching.
        """
        # 1. Primary lookup: Permanent AICTE Identifier (supports DEMO and INST aliases)
        if identifier:
            cleaned_id = identifier.strip().upper()
            alias_id = cleaned_id.replace("AICTE-DEMO-", "AICTE-INST-")
            alt_alias_id = cleaned_id.replace("AICTE-INST-", "AICTE-DEMO-")
            ref = db.query(InstitutionReferenceRecord).filter(
                or_(
                    func.upper(InstitutionReferenceRecord.aicte_permanent_id) == cleaned_id,
                    func.upper(InstitutionReferenceRecord.aicte_permanent_id) == alias_id,
                    func.upper(InstitutionReferenceRecord.aicte_permanent_id) == alt_alias_id,
                )
            ).first()
            if ref:
                return ref

        # 2. Normalized fallback lookup
        if name and city and state:
            norm_name = normalize_institution_field(name)
            norm_city = normalize_institution_field(city)
            norm_state = normalize_institution_field(state)

            ref = db.query(InstitutionReferenceRecord).filter(
                and_(
                    InstitutionReferenceRecord.normalized_name == norm_name,
                    InstitutionReferenceRecord.normalized_city == norm_city,
                    InstitutionReferenceRecord.normalized_state == norm_state,
                )
            ).first()
            if ref:
                return ref

        # 3. Normalized name-only fallback
        if name:
            norm_name = normalize_institution_field(name)
            ref = db.query(InstitutionReferenceRecord).filter(
                InstitutionReferenceRecord.normalized_name == norm_name
            ).first()
            if ref:
                return ref

        return None

    @classmethod
    def match_application_against_reference(
        cls, db: Session, application_id: str
    ) -> Dict[str, Any]:
        """
        Executes comprehensive reference matching for an application:
        - Resolves official reference record.
        - Compares institution identity, address, and legal standing.
        - Audits approval history continuity across academic years.
        - Verifies sanctioned intakes and quota eligibility.
        - Emits explainable findings with source provenance and timestamps.
        """
        cls.seed_authoritative_benchmarks(db)

        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        inst = app.institution
        ref = cls.find_reference_record(
            db=db,
            identifier=inst.institution_identifier,
            name=inst.name,
            city=inst.city,
            state=inst.state,
        )

        matched_fields: Dict[str, Dict[str, Any]] = {}
        findings: List[Dict[str, Any]] = []

        # ===================================================================
        # CASE 1: UNRESOLVED — No official reference record found
        # ===================================================================
        if not ref:
            matched_fields["identifier"] = {
                "submitted_value": inst.institution_identifier,
                "official_value": None,
                "match": False,
                "confidence": 0.0,
                "notes": "Identifier not present in AICTE Regulatory Registry.",
            }
            matched_fields["name"] = {
                "submitted_value": inst.name,
                "official_value": None,
                "match": False,
                "confidence": 0.0,
                "notes": "Name not matched in official reference records.",
            }
            findings.append({
                "finding_type": "REFERENCE_NOT_FOUND",
                "severity": "WARNING",
                "message": (
                    f"No official AICTE reference ledger record found for identifier '{inst.institution_identifier}' "
                    f"or name '{inst.name}'. Submitted data is self-reported and unverified; manual officer scrutiny required."
                ),
                "reference_source": "AICTE Central Regulatory Registry",
                "effective_date": datetime.utcnow().strftime("%Y-%m-%d"),
            })
            return {
                "application_id": app.id,
                "institution_id": inst.id,
                "reference_matched": False,
                "institution_reference_id": None,
                "aicte_permanent_id": None,
                "legal_name": None,
                "verification_status": "UNRESOLVED_MANUAL_REVIEW",
                "source_provenance": None,
                "data_freshness_date": None,
                "is_official": False,
                "standing_status": None,
                "matched_fields": matched_fields,
                "findings": findings,
                "programmes_summary": [],
                "latest_approval": None,
                "recommendation": "MANUAL_SCRUTINY_REQUIRED",
            }

        # ===================================================================
        # CASE 2: REFERENCE MATCHED — Cross-verify details
        # ===================================================================
        # 1. Identity field matching
        name_match = (normalize_institution_field(inst.name) == ref.normalized_name)
        matched_fields["name"] = {
            "submitted_value": inst.name,
            "official_value": ref.legal_name,
            "match": name_match,
            "confidence": 1.0 if name_match else 0.5,
            "notes": "Exact match with registered legal name" if name_match else "Name discrepancy detected against official registry",
        }
        if not name_match:
            findings.append({
                "finding_type": "REFERENCE_MISMATCH",
                "severity": "CRITICAL",
                "message": f"Submitted institution name '{inst.name}' does not match official registered legal name '{ref.legal_name}'.",
                "reference_source": ref.source_provenance,
                "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d"),
            })

        city_match = (normalize_institution_field(inst.city) == ref.normalized_city)
        matched_fields["city"] = {
            "submitted_value": inst.city,
            "official_value": ref.district_or_city,
            "match": city_match,
            "confidence": 1.0 if city_match else 0.6,
        }

        state_match = (normalize_institution_field(inst.state) == ref.normalized_state)
        matched_fields["state"] = {
            "submitted_value": inst.state,
            "official_value": ref.state,
            "match": state_match,
            "confidence": 1.0 if state_match else 0.6,
        }

        # 2. Institutional Standing Check
        if ref.standing_status != "Approved":
            findings.append({
                "finding_type": "ADVERSE_STANDING",
                "severity": "CRITICAL",
                "message": f"Institution standing status in official registry is '{ref.standing_status}'. Normal automated processing suspended.",
                "reference_source": ref.source_provenance,
                "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d"),
            })

        # 3. Approval Continuity Check
        # For Extension of Approval (EoA) in 2026-2027, institution must have approved status in 2025-2026
        latest_approval = db.query(InstitutionApprovalHistory).filter(
            InstitutionApprovalHistory.institution_reference_id == ref.id
        ).order_by(InstitutionApprovalHistory.academic_year.desc()).first()

        if not latest_approval:
            findings.append({
                "finding_type": "NO_APPROVAL_HISTORY",
                "severity": "CRITICAL",
                "message": "Institution has no previous approval history on record. Extension of Approval requires prior continuous approvals.",
                "reference_source": ref.source_provenance,
                "effective_date": None,
            })
        elif latest_approval.academic_year != "2025-2026":
            findings.append({
                "finding_type": "OUTDATED_APPROVAL",
                "severity": "WARNING",
                "message": (
                    f"Latest official approval on record is for AY {latest_approval.academic_year}. "
                    f"Approval gap detected prior to current AY {app.academic_year}. Manual inspection of restoration/restoration orders required."
                ),
                "reference_source": ref.source_provenance,
                "effective_date": latest_approval.effective_end_date.strftime("%Y-%m-%d"),
            })
        else:
            findings.append({
                "finding_type": "REFERENCE_VERIFIED",
                "severity": "INFO",
                "message": f"Continuous approval verified: Valid Extension of Approval on record for AY {latest_approval.academic_year} (Total Sanctioned Intake: {latest_approval.total_sanctioned_intake}).",
                "reference_source": ref.source_provenance,
                "effective_date": latest_approval.effective_start_date.strftime("%Y-%m-%d"),
            })

        # 4. Quota Verification (NRI / FN Quota applications)
        active_programmes = db.query(ApprovedProgrammeReference).filter(
            ApprovedProgrammeReference.institution_reference_id == ref.id,
            ApprovedProgrammeReference.is_active == True,
        ).all()

        if app.application_category == "NRI / Foreign National Quota":
            has_quota_approval = any(p.nri_quota_approved or p.pio_fn_quota_approved for p in active_programmes)
            if not has_quota_approval:
                findings.append({
                    "finding_type": "UNAPPROVED_QUOTA",
                    "severity": "CRITICAL",
                    "message": "Institution has submitted an NRI / Foreign National Quota application, but regulatory records show no existing approved quota allocation for any active programme.",
                    "reference_source": ref.source_provenance,
                    "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d") if ref.data_freshness_date else None,
                })
            else:
                findings.append({
                    "finding_type": "REFERENCE_VERIFIED",
                    "severity": "INFO",
                    "message": "Verified official reference records confirm prior approval for NRI / PIO / FN quota seats.",
                    "reference_source": ref.source_provenance,
                    "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d") if ref.data_freshness_date else None,
                })

        # 5. Programme and Sanctioned Intake Verification (Increase in Intake category)
        if app.application_category == "Increase in Intake":
            if not active_programmes:
                findings.append({
                    "finding_type": "PROGRAMME_INTAKE_MISMATCH",
                    "severity": "CRITICAL",
                    "message": "Application submitted for Increase in Intake, but reference ledger records zero approved active programmes for this institution.",
                    "reference_source": ref.source_provenance,
                    "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d") if ref.data_freshness_date else None,
                })
            else:
                nba_progs = [p for p in active_programmes if p.accreditation_status and "NBA" in p.accreditation_status.upper()]
                if not nba_progs:
                    findings.append({
                        "finding_type": "PROGRAMME_INTAKE_MISMATCH",
                        "severity": "WARNING",
                        "message": "AICTE Chapter II norms mandate valid NBA accreditation for intake expansion. None of the active programmes on record hold valid NBA accreditation.",
                        "reference_source": ref.source_provenance,
                        "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d") if ref.data_freshness_date else None,
                    })
                else:
                    findings.append({
                        "finding_type": "REFERENCE_VERIFIED",
                        "severity": "INFO",
                        "message": f"Accreditation prerequisite verified: {len(nba_progs)} approved programme(s) have NBA accreditation eligible for intake expansion.",
                        "reference_source": ref.source_provenance,
                        "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d") if ref.data_freshness_date else None,
                    })

        # 6. Authenticity Guard: Synthetic Demonstration Benchmark vs Official Statutory Record
        if not ref.is_official or ref.verification_status != "OFFICIAL_VERIFIED":
            findings.append({
                "finding_type": "SYNTHETIC_REFERENCE_BENCHMARK",
                "severity": "WARNING",
                "message": (
                    f"Reference record for '{ref.aicte_permanent_id}' is a synthetic demonstration benchmark, "
                    "not an authentic live AICTE Central Portal record. Cannot establish official statutory verification. "
                    "Routing to Manual Scrutiny Queue."
                ),
                "reference_source": ref.source_provenance,
                "effective_date": ref.data_freshness_date.strftime("%Y-%m-%d") if ref.data_freshness_date else None,
            })

        # Determine overall recommendation
        has_critical = any(f["severity"] == "CRITICAL" for f in findings)
        has_warning = any(f["severity"] == "WARNING" for f in findings)

        if has_critical:
            recommendation = "REJECT_UNAUTHORIZED"
            status_str = "MISMATCH_DETECTED"
        elif not ref.is_official or ref.verification_status == "SYNTHETIC_BENCHMARK":
            # Synthetic benchmarks must NEVER produce an official verification outcome
            recommendation = "MANUAL_SCRUTINY_REQUIRED"
            status_str = "SYNTHETIC_BENCHMARK"
        elif has_warning:
            recommendation = "MANUAL_SCRUTINY_REQUIRED"
            status_str = "PROVISIONAL_PENDING"
        else:
            recommendation = "AUTO_VERIFIED"
            status_str = "OFFICIAL_VERIFIED"

        prog_summaries = [
            {
                "id": p.id,
                "programme_name": p.programme_name,
                "course_name": p.course_name,
                "level": p.level,
                "approved_intake": p.approved_intake,
                "nri_quota_approved": p.nri_quota_approved,
                "nri_quota_intake": p.nri_quota_intake,
                "pio_fn_quota_approved": p.pio_fn_quota_approved,
                "pio_fn_quota_intake": p.pio_fn_quota_intake,
                "accreditation_status": p.accreditation_status,
                "accreditation_valid_until": p.accreditation_valid_until,
                "academic_year": p.academic_year,
                "is_active": p.is_active,
            }
            for p in active_programmes
        ]

        latest_approval_dict = None
        if latest_approval:
            latest_approval_dict = {
                "id": latest_approval.id,
                "academic_year": latest_approval.academic_year,
                "eoa_application_number": latest_approval.eoa_application_number,
                "eoa_issue_date": latest_approval.eoa_issue_date,
                "effective_start_date": latest_approval.effective_start_date,
                "effective_end_date": latest_approval.effective_end_date,
                "total_sanctioned_intake": latest_approval.total_sanctioned_intake,
                "approval_type": latest_approval.approval_type,
                "issuing_authority": latest_approval.issuing_authority,
                "is_latest": latest_approval.is_latest,
            }

        return {
            "application_id": app.id,
            "institution_id": inst.id,
            "reference_matched": True,
            "institution_reference_id": ref.id,
            "aicte_permanent_id": ref.aicte_permanent_id,
            "legal_name": ref.legal_name,
            "verification_status": status_str,
            "source_provenance": ref.source_provenance,
            "data_freshness_date": ref.data_freshness_date,
            "is_official": ref.is_official,
            "standing_status": ref.standing_status,
            "matched_fields": matched_fields,
            "findings": findings,
            "programmes_summary": prog_summaries,
            "latest_approval": latest_approval_dict,
            "recommendation": recommendation,
        }
