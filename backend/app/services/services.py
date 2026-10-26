import random
import string
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from sqlalchemy.exc import IntegrityError

from app.models.models import (
    Application,
    Institution,
    Document,
    Finding,
    RiskAssessment,
    AuditEvent,
    normalize_institution_field,
)
from app.schemas.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    InstitutionCreate,
    InstitutionUpdate,
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    TrendPoint,
)


class DuplicateInstitutionError(Exception):
    """Raised when an institution conflicts with an existing record by identifier or normalized name/location."""
    pass


def generate_application_id() -> str:
    # Format: AICTE-2026-XXXXX
    digits = "".join(random.choices(string.digits, k=5))
    return f"AICTE-2026-{digits}"


class ApplicationService:
    @staticmethod
    def get_applications(
        db: Session,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        academic_year: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = db.query(Application).join(Institution, Application.institution_id == Institution.id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Application.application_identifier.ilike(search_term),
                    Institution.name.ilike(search_term),
                    Institution.institution_identifier.ilike(search_term),
                    Institution.city.ilike(search_term),
                )
            )

        if status and status != "All":
            query = query.filter(Application.status == status)

        if category and category != "All":
            query = query.filter(Application.application_category == category)

        if academic_year and academic_year != "All":
            query = query.filter(Application.academic_year == academic_year)

        total = query.count()
        offset = (page - 1) * limit
        apps = (
            query.order_by(desc(Application.submission_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for app in apps:
            items.append({
                "id": app.id,
                "application_identifier": app.application_identifier,
                "institution_id": app.institution_id,
                "institution_name": app.institution.name if app.institution else "Unknown",
                "institution_state": app.institution.state if app.institution else "",
                "institution_city": app.institution.city if app.institution else "",
                "application_category": app.application_category,
                "academic_year": app.academic_year,
                "status": app.status,
                "submission_date": app.submission_date,
                "created_at": app.created_at,
                "documents_count": len(app.documents) if app.documents else 0,
                "findings_count": len(app.findings) if app.findings else 0,
            })

        return items, total

    @staticmethod
    def get_application_by_id(db: Session, application_id: str) -> Optional[dict]:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return None

        # Build response dict
        return {
            "id": app.id,
            "application_identifier": app.application_identifier,
            "institution_id": app.institution_id,
            "institution_name": app.institution.name if app.institution else None,
            "institution_type": app.institution.institution_type if app.institution else None,
            "institution_state": app.institution.state if app.institution else None,
            "institution_city": app.institution.city if app.institution else None,
            "application_category": app.application_category,
            "academic_year": app.academic_year,
            "status": app.status,
            "submission_date": app.submission_date,
            "assigned_reviewer_id": app.assigned_reviewer_id,
            "assigned_reviewer_name": app.assigned_reviewer.name if app.assigned_reviewer else None,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "documents": [
                {
                    "id": doc.id,
                    "application_id": doc.application_id,
                    "document_type": doc.document_type,
                    "original_filename": doc.original_filename,
                    "file_size_bytes": doc.file_size_bytes,
                    "detected_mime_type": doc.detected_mime_type,
                    "sha256_hash": doc.sha256_hash,
                    "version": doc.version,
                    "replaces_document_id": doc.replaces_document_id,
                    "processing_status": doc.processing_status,
                    "processing_error": doc.processing_error,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                }
                for doc in app.documents
            ],
            "findings": [
                {
                    "id": f.id,
                    "application_id": f.application_id,
                    "category": f.category,
                    "severity": f.severity,
                    "title": f.title,
                    "explanation": f.explanation,
                    "status": f.status,
                    "created_at": f.created_at,
                }
                for f in app.findings
            ],
            "risk_assessments": [
                {
                    "id": r.id,
                    "application_id": r.application_id,
                    "assessment_level": r.assessment_level,
                    "score": r.score,
                    "risk_band": r.risk_band,
                    "factor_breakdown": r.factor_breakdown,
                    "evidence_coverage": r.evidence_coverage,
                    "calculated_at": r.calculated_at,
                }
                for r in app.risk_assessments
            ],
        }

    @staticmethod
    def create_application(db: Session, app_data: ApplicationCreate) -> Application:
        # Check institution exists
        inst = db.query(Institution).filter(Institution.id == app_data.institution_id).first()
        if not inst:
            raise ValueError(f"Institution with id {app_data.institution_id} not found")

        app_id = app_data.application_identifier or generate_application_id()

        # Check duplicate
        exists = db.query(Application).filter(Application.application_identifier == app_id).first()
        if exists:
            app_id = generate_application_id()

        db_app = Application(
            application_identifier=app_id,
            institution_id=app_data.institution_id,
            application_category=app_data.application_category,
            academic_year=app_data.academic_year,
            status="Under Validation",
            submission_date=datetime.utcnow(),
        )
        db.add(db_app)
        db.flush()

        # Create audit event
        audit = AuditEvent(
            entity_type="Application",
            entity_id=db_app.id,
            action="CREATE",
            details={
                "application_identifier": db_app.application_identifier,
                "institution_id": db_app.institution_id,
                "category": db_app.application_category,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(db_app)
        return db_app

    @staticmethod
    def update_application(db: Session, application_id: str, app_update: ApplicationUpdate) -> Optional[Application]:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return None

        update_dict = app_update.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(app, key, val)

        app.updated_at = datetime.utcnow()

        audit = AuditEvent(
            entity_type="Application",
            entity_id=app.id,
            action="UPDATE",
            details=update_dict,
        )
        db.add(audit)
        db.commit()
        db.refresh(app)
        return app


class InstitutionService:
    @staticmethod
    def get_institutions(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = db.query(Institution)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Institution.name.ilike(term),
                    Institution.institution_identifier.ilike(term),
                    Institution.city.ilike(term),
                    Institution.state.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * limit
        institutions = (
            query.order_by(Institution.name)
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for inst in institutions:
            items.append({
                "id": inst.id,
                "institution_identifier": inst.institution_identifier,
                "name": inst.name,
                "institution_type": inst.institution_type,
                "state": inst.state,
                "city": inst.city,
                "created_at": inst.created_at,
                "updated_at": inst.updated_at,
                "application_count": len(inst.applications) if inst.applications else 0,
            })

        return items, total

    @staticmethod
    def create_institution(db: Session, data: InstitutionCreate) -> Institution:
        norm_name = normalize_institution_field(data.name)
        norm_city = normalize_institution_field(data.city)
        norm_state = normalize_institution_field(data.state)
        norm_identifier = data.institution_identifier.strip().upper()

        # 1. Check duplicate official AICTE identifier
        existing_id = db.query(Institution).filter(
            func.upper(Institution.institution_identifier) == norm_identifier
        ).first()
        if existing_id:
            raise DuplicateInstitutionError(
                f"Institution with official identifier '{norm_identifier}' already exists."
            )

        # 2. Check duplicate normalized name within same district/city and state
        existing_loc = db.query(Institution).filter(
            Institution.normalized_name == norm_name,
            Institution.normalized_city == norm_city,
            Institution.normalized_state == norm_state,
        ).first()
        if existing_loc:
            raise DuplicateInstitutionError(
                f"Institution '{data.name.strip()}' already exists in {data.city.strip()}, {data.state.strip()}. "
                "Institutions with the same normalized name in the same district and state are prohibited."
            )

        inst = Institution(
            institution_identifier=norm_identifier,
            name=data.name.strip(),
            institution_type=data.institution_type.strip(),
            state=data.state.strip(),
            city=data.city.strip(),
            normalized_name=norm_name,
            normalized_city=norm_city,
            normalized_state=norm_state,
        )
        db.add(inst)
        try:
            db.flush()
        except IntegrityError as e:
            db.rollback()
            raise DuplicateInstitutionError(
                "Duplicate institution conflict: An institution with this name in this district/state or identifier already exists."
            ) from e

        audit = AuditEvent(
            entity_type="Institution",
            entity_id=inst.id,
            action="CREATE",
            details={
                "identifier": inst.institution_identifier,
                "name": inst.name,
                "city": inst.city,
                "state": inst.state,
            },
        )
        db.add(audit)
        try:
            db.commit()
            db.refresh(inst)
        except IntegrityError as e:
            db.rollback()
            raise DuplicateInstitutionError(
                "Duplicate institution conflict detected during transaction commit."
            ) from e
        return inst

    @staticmethod
    def update_institution(db: Session, institution_id: str, data: InstitutionUpdate) -> Institution:
        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            raise ValueError(f"Institution with ID '{institution_id}' not found")

        target_name = data.name.strip() if data.name is not None else inst.name
        target_city = data.city.strip() if data.city is not None else inst.city
        target_state = data.state.strip() if data.state is not None else inst.state
        target_identifier = data.institution_identifier.strip().upper() if data.institution_identifier is not None else inst.institution_identifier

        norm_name = normalize_institution_field(target_name)
        norm_city = normalize_institution_field(target_city)
        norm_state = normalize_institution_field(target_state)

        # 1. Check duplicate identifier on another record
        if target_identifier != inst.institution_identifier:
            conflict_id = db.query(Institution).filter(
                Institution.id != institution_id,
                func.upper(Institution.institution_identifier) == target_identifier
            ).first()
            if conflict_id:
                raise DuplicateInstitutionError(
                    f"Institution with official identifier '{target_identifier}' already exists."
                )

        # 2. Check duplicate normalized name/location on another record
        if (norm_name != inst.normalized_name or norm_city != inst.normalized_city or norm_state != inst.normalized_state):
            conflict_loc = db.query(Institution).filter(
                Institution.id != institution_id,
                Institution.normalized_name == norm_name,
                Institution.normalized_city == norm_city,
                Institution.normalized_state == norm_state,
            ).first()
            if conflict_loc:
                raise DuplicateInstitutionError(
                    f"Institution '{target_name}' already exists in {target_city}, {target_state}. "
                    "Institutions with the same normalized name in the same district and state are prohibited."
                )

        # Apply updates
        if data.name is not None:
            inst.name = target_name
            inst.normalized_name = norm_name
        if data.city is not None:
            inst.city = target_city
            inst.normalized_city = norm_city
        if data.state is not None:
            inst.state = target_state
            inst.normalized_state = norm_state
        if data.institution_identifier is not None:
            inst.institution_identifier = target_identifier
        if data.institution_type is not None:
            inst.institution_type = data.institution_type.strip()

        try:
            db.flush()
        except IntegrityError as e:
            db.rollback()
            raise DuplicateInstitutionError(
                "Duplicate institution conflict: An institution with this name in this district/state or identifier already exists."
            ) from e

        audit = AuditEvent(
            entity_type="Institution",
            entity_id=inst.id,
            action="UPDATE",
            details={
                "identifier": inst.institution_identifier,
                "name": inst.name,
                "city": inst.city,
                "state": inst.state,
            },
        )
        db.add(audit)
        try:
            db.commit()
            db.refresh(inst)
        except IntegrityError as e:
            db.rollback()
            raise DuplicateInstitutionError(
                "Duplicate institution conflict detected during transaction commit."
            ) from e
        return inst


class DashboardService:
    @staticmethod
    def get_summary(db: Session) -> DashboardSummaryResponse:
        total_apps = db.query(func.count(Application.id)).scalar() or 0
        in_validation = db.query(func.count(Application.id)).filter(
            Application.status.in_(["Under Validation", "Submitted", "Running"])
        ).scalar() or 0
        action_required = db.query(func.count(Application.id)).filter(
            Application.status.in_(["Action Required", "Discrepancy", "Clarification Requested"])
        ).scalar() or 0
        verified_docs = db.query(func.count(Document.id)).filter(
            Document.processing_status == "Verified"
        ).scalar() or 0

        # Breakdowns for donut chart
        statuses = ["Verified", "Under Validation", "Action Required", "Approved", "Rejected"]
        status_breakdown = {}
        for s in statuses:
            count = db.query(func.count(Application.id)).filter(Application.status == s).scalar() or 0
            status_breakdown[s] = count

        # Aggregated risk breakdown from persisted assessments
        risk_breakdown = {"Low": 0, "Medium": 0, "High": 0}
        # Get latest assessment per application
        latest_risk_subq = (
            db.query(
                RiskAssessment.application_id,
                func.max(RiskAssessment.calculated_at).label("max_calc"),
            )
            .group_by(RiskAssessment.application_id)
            .subquery()
        )
        latest_risks = (
            db.query(RiskAssessment.risk_band, func.count(RiskAssessment.id))
            .join(
                latest_risk_subq,
                (RiskAssessment.application_id == latest_risk_subq.c.application_id)
                & (RiskAssessment.calculated_at == latest_risk_subq.c.max_calc),
            )
            .group_by(RiskAssessment.risk_band)
            .all()
        )
        for band, count in latest_risks:
            if band in risk_breakdown:
                risk_breakdown[band] = count

        return DashboardSummaryResponse(
            total_applications=total_apps,
            in_validation=in_validation,
            action_required=action_required,
            verified_documents=verified_docs,
            status_breakdown=status_breakdown,
            risk_breakdown=risk_breakdown,
        )

    @staticmethod
    def get_trends(db: Session, days: int = 14) -> DashboardTrendsResponse:
        # Aggregate real applications submitted over the past N days
        now = datetime.utcnow()
        start_date = now - timedelta(days=days - 1)

        # Generate date points for each day
        trend_points = []
        for i in range(days):
            day_start = (start_date + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            date_str = day_start.strftime("%b %d")

            app_count = db.query(func.count(Application.id)).filter(
                Application.submission_date >= day_start,
                Application.submission_date < day_end,
            ).scalar() or 0

            verified_count = db.query(func.count(Application.id)).filter(
                Application.status == "Verified",
                Application.updated_at >= day_start,
                Application.updated_at < day_end,
            ).scalar() or 0

            trend_points.append(TrendPoint(date=date_str, applications=app_count, verified=verified_count))

        return DashboardTrendsResponse(trends=trend_points)
