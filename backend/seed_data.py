import os
import sys
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.models import (
    User,
    Institution,
    Application,
    Document,
    ValidationRule,
    Finding,
    RiskAssessment,
)

def seed():
    db = SessionLocal()
    try:
        print("[SEED] Checking existing database records...")
        inst_count = db.query(Institution).count()
        if inst_count > 0:
            print(f"[SEED] Database already contains {inst_count} institutions. Skipping seed.")
            return

        print("[SEED] Seeding demo institutions (clearly labeled synthetic demo records)...")
        # 1. Institutions
        institutions_data = [
            {
                "institution_identifier": "AICTE-INST-001",
                "name": "Delhi Institute of Technology & Advanced Sciences",
                "institution_type": "Engineering",
                "state": "Delhi",
                "city": "New Delhi",
            },
            {
                "institution_identifier": "AICTE-INST-002",
                "name": "Maharashtra Institute of Technology & Research",
                "institution_type": "Engineering",
                "state": "Maharashtra",
                "city": "Pune",
            },
            {
                "institution_identifier": "AICTE-INST-003",
                "name": "Karnataka Global School of Management",
                "institution_type": "Management",
                "state": "Karnataka",
                "city": "Bengaluru",
            },
            {
                "institution_identifier": "AICTE-INST-004",
                "name": "Tamil Nadu College of Pharmacy & Research",
                "institution_type": "Pharmacy",
                "state": "Tamil Nadu",
                "city": "Chennai",
            },
            {
                "institution_identifier": "AICTE-INST-005",
                "name": "Gujarat State Polytechnic College",
                "institution_type": "Polytechnic",
                "state": "Gujarat",
                "city": "Ahmedabad",
            },
        ]

        inst_objs = []
        for d in institutions_data:
            inst = Institution(**d)
            db.add(inst)
            inst_objs.append(inst)
        db.flush()

        print("[SEED] Seeding sample AICTE validation rules...")
        rules_data = [
            {
                "rule_code": "LAND-NORM-01",
                "name": "Minimum Land Area Norm",
                "description": "Verification of contiguous land ownership deed as per AICTE Approval Process Handbook",
                "category": "Regulatory",
                "severity": "Critical",
                "weight": 2.5,
            },
            {
                "rule_code": "FIRE-NOC-02",
                "name": "Valid Fire Safety NOC",
                "description": "Validation of fire NOC authenticity, issuing jurisdiction, and valid validity timeframe",
                "category": "Safety",
                "severity": "High",
                "weight": 2.0,
            },
            {
                "rule_code": "BLD-PLAN-03",
                "name": "Competent Authority Building Plan Approval",
                "description": "Verification of sanction order and total built-up area matching instructional area requirements",
                "category": "Infrastructure",
                "severity": "High",
                "weight": 1.5,
            },
        ]
        for r in rules_data:
            rule = ValidationRule(
                rule_code=r["rule_code"],
                name=r["name"],
                description=r["description"],
                severity=r["severity"],
                weight=r["weight"],
                is_active=True,
            )
            db.add(rule)
        db.flush()

        print("[SEED] Seeding initial applications with timeline distributions...")
        # Applications
        apps_data = [
            {
                "application_identifier": "APP-2026-08492",
                "institution": inst_objs[0],
                "category": "Extension of Approval (EoA)",
                "academic_year": "2026-2027",
                "status": "Verified",
                "days_ago": 6,
            },
            {
                "application_identifier": "APP-2026-08493",
                "institution": inst_objs[1],
                "category": "Increase in Intake",
                "academic_year": "2026-2027",
                "status": "Under Validation",
                "days_ago": 4,
            },
            {
                "application_identifier": "APP-2026-08494",
                "institution": inst_objs[2],
                "category": "New Institute",
                "academic_year": "2026-2027",
                "status": "Action Required",
                "days_ago": 2,
            },
            {
                "application_identifier": "APP-2026-08495",
                "institution": inst_objs[3],
                "category": "Extension of Approval (EoA)",
                "academic_year": "2026-2027",
                "status": "Under Validation",
                "days_ago": 1,
            },
            {
                "application_identifier": "APP-2026-08496",
                "institution": inst_objs[4],
                "category": "Extension of Approval (EoA)",
                "academic_year": "2026-2027",
                "status": "Verified",
                "days_ago": 0,
            },
        ]

        for item in apps_data:
            sub_date = datetime.utcnow() - timedelta(days=item["days_ago"], hours=3)
            app = Application(
                application_identifier=item["application_identifier"],
                institution_id=item["institution"].id,
                application_category=item["category"],
                academic_year=item["academic_year"],
                status=item["status"],
                submission_date=sub_date,
            )
            db.add(app)
            db.flush()

            # Add documents
            doc1 = Document(
                application_id=app.id,
                document_type="Land Title Certificate",
                original_filename=f"{app.application_identifier}_Land_Deed.pdf",
                processing_status="Verified" if item["status"] == "Verified" else "Pending",
            )
            doc2 = Document(
                application_id=app.id,
                document_type="Fire Safety NOC",
                original_filename=f"{app.application_identifier}_Fire_NOC.pdf",
                processing_status="Verified" if item["status"] == "Verified" else "Pending",
            )
            db.add_all([doc1, doc2])
            db.flush()

            # Add finding for Action Required
            if item["status"] == "Action Required":
                finding = Finding(
                    application_id=app.id,
                    document_id=doc2.id,
                    rule_code="FIRE-NOC-02",
                    category="Safety Compliance",
                    severity="High",
                    title="Fire Safety NOC Expiry Discrepancy",
                    explanation="Submitted Fire NOC expired prior to academic cycle commencement date. Updated certificate from State Fire Services required.",
                    status="Open",
                )
                db.add(finding)

                risk = RiskAssessment(
                    application_id=app.id,
                    assessment_level="Application",
                    score=68.5,
                    risk_band="Medium",
                    factor_breakdown={"safety_compliance": 0.4, "regulatory_history": 0.1},
                    evidence_coverage=85.0,
                    assessment_version="1.0",
                )
                db.add(risk)

        db.commit()
        print("[SEED] Demo records seeded successfully into database!")
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Error during seed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
