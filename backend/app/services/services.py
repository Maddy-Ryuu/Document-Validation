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
    InstitutionReferenceRecord,
    Document,
    Finding,
    RiskAssessment,
    AuditEvent,
    DocumentExtraction,
    ReviewAction,
    User,
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

    @staticmethod
    def delete_application(db: Session, application_id: str, authorized_user: Optional[str] = None) -> bool:
        """
        Deletes an application after preserving full forensic audit history and linked
        document metadata according to the statutory retention policy.
        """
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return False

        # Gather linked documents summary for forensic retention
        docs = db.query(Document).filter(Document.application_id == application_id).all()
        retained_docs_summary = [
            {
                "id": d.id,
                "document_type": d.document_type,
                "filename": d.original_filename,
                "sha256": d.sha256_hash,
                "version": d.version,
            }
            for d in docs
        ]

        # Record indelible audit event
        audit = AuditEvent(
            entity_type="Application",
            entity_id=application_id,
            action="APPLICATION_DELETE",
            details={
                "application_identifier": app.application_identifier,
                "institution_id": app.institution_id,
                "institution_name": app.institution.name if app.institution else "Unknown",
                "category": app.application_category,
                "status": app.status,
                "authorized_by": authorized_user or "AICTE Scrutiny Officer",
                "retention_policy": "FORENSIC_AUDIT_LOG_PRESERVED",
                "retained_documents_count": len(retained_docs_summary),
                "retained_documents": retained_docs_summary,
            },
        )
        db.add(audit)
        db.delete(app)
        db.commit()
        return True


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

    @staticmethod
    def delete_institution(
        db: Session,
        institution_id: str,
        authorized_user: Optional[str] = None,
        authorized_role: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Deletes an operational institution record after verifying eligibility:
        1. Checks whether the ID belongs to an authoritative reference record (protected).
        2. Checks whether linked applications exist (prevents deletion to avoid orphaned records).
        3. Records an indelible AuditEvent with action='INSTITUTION_DELETE'.
        4. Does NOT cascade delete applications, documents, or reference records.
        """
        # Guard: Check if id belongs to an authoritative reference record
        ref_record = db.query(InstitutionReferenceRecord).filter(InstitutionReferenceRecord.id == institution_id).first()
        if ref_record:
            return False, "PROTECTED_REFERENCE_RECORD: Authoritative regulatory reference records cannot be deleted through the operational institution interface."

        inst = db.query(Institution).filter(Institution.id == institution_id).first()
        if not inst:
            return False, "NOT_FOUND"

        # Guard: Linked applications check
        linked_apps_count = db.query(Application).filter(Application.institution_id == institution_id).count()
        if linked_apps_count > 0:
            return False, f"LINKED_RECORDS_EXIST: Cannot delete institution '{inst.name}' ({inst.institution_identifier}): {linked_apps_count} active application(s) exist. Applications and linked statutory documents must be resolved or deleted first to prevent orphaned records."

        # Record indelible audit event
        audit = AuditEvent(
            entity_type="Institution",
            entity_id=inst.id,
            action="INSTITUTION_DELETE",
            details={
                "institution_identifier": inst.institution_identifier,
                "name": inst.name,
                "institution_type": inst.institution_type,
                "state": inst.state,
                "city": inst.city,
                "authorized_by": authorized_user or "AICTE Administrator",
                "authorized_role": authorized_role or "admin",
                "timestamp": datetime.utcnow().isoformat(),
                "retention_policy": "FORENSIC_AUDIT_LOG_PRESERVED",
            },
        )
        db.add(audit)
        db.delete(inst)
        db.commit()
        return True, None


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


class DocumentService:
    @staticmethod
    def get_documents(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        document_type: Optional[str] = None,
        application_id: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = (
            db.query(Document)
            .join(Application, Document.application_id == Application.id)
            .join(Institution, Application.institution_id == Institution.id)
        )

        if application_id:
            query = query.filter(Document.application_id == application_id)
        if status and status != "All":
            query = query.filter(Document.processing_status == status)
        if document_type and document_type != "All":
            query = query.filter(Document.document_type == document_type)
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Document.original_filename.ilike(term),
                    Document.document_type.ilike(term),
                    Application.application_identifier.ilike(term),
                    Institution.name.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * limit
        docs = query.order_by(desc(Document.created_at)).offset(offset).limit(limit).all()

        items = []
        for d in docs:
            ext = d.extractions[0] if d.extractions else None
            items.append({
                "id": d.id,
                "application_id": d.application_id,
                "application_identifier": d.application.application_identifier if d.application else None,
                "institution_id": d.application.institution_id if d.application else None,
                "institution_name": d.application.institution.name if d.application and d.application.institution else None,
                "document_type": d.document_type,
                "original_filename": d.original_filename,
                "file_size_bytes": d.file_size_bytes,
                "detected_mime_type": d.detected_mime_type,
                "sha256_hash": d.sha256_hash,
                "version": d.version,
                "processing_status": d.processing_status,
                "processing_error": d.processing_error,
                "confidence_score": ext.confidence_score if ext else None,
                "extraction_status": ext.extraction_status if ext else None,
                "structured_fields": ext.structured_fields if ext else None,
                "findings_count": len(d.findings) if d.findings else 0,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            })
        return items, total

    @staticmethod
    def review_document(
        db: Session,
        document_id: str,
        action: str,  # "Approved", "Rejected", "Needs Review"
        comments: Optional[str] = None,
    ) -> Optional[dict]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return None

        status_map = {
            "Approved": "Processed",
            "Rejected": "Failed",
            "Needs Review": "Needs Review",
        }
        new_status = status_map.get(action, "Needs Review")
        old_status = doc.processing_status
        doc.processing_status = new_status
        doc.updated_at = datetime.utcnow()

        audit = AuditEvent(
            entity_type="Document",
            entity_id=doc.id,
            action=f"REVIEW_{action.upper().replace(' ', '_')}",
            details={
                "action": action,
                "previous_status": old_status,
                "new_status": new_status,
                "comments": comments or "",
                "filename": doc.original_filename,
                "document_type": doc.document_type,
                "application_id": doc.application_id,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)

        return {
            "id": doc.id,
            "application_id": doc.application_id,
            "document_type": doc.document_type,
            "original_filename": doc.original_filename,
            "processing_status": doc.processing_status,
            "updated_at": doc.updated_at,
        }


class QueueService:
    @staticmethod
    def get_review_queue(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = db.query(Application).join(Institution, Application.institution_id == Institution.id)

        if status and status != "All":
            query = query.filter(Application.status == status)
        else:
            query = query.filter(Application.status.in_(["Action Required", "Under Validation", "Needs Review"]))

        if category and category != "All":
            query = query.filter(Application.application_category == category)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Application.application_identifier.ilike(term),
                    Institution.name.ilike(term),
                    Institution.city.ilike(term),
                    Institution.state.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * limit
        apps = query.order_by(desc(Application.submission_date)).offset(offset).limit(limit).all()

        items = []
        for app in apps:
            latest_risk = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.application_id == app.id)
                .order_by(desc(RiskAssessment.calculated_at))
                .first()
            )
            risk_band = latest_risk.risk_band if latest_risk else "Unevaluated"
            risk_score = latest_risk.score if latest_risk else None

            computed_priority = "Medium"
            if risk_band in ("High", "Extreme") or app.status == "Action Required":
                computed_priority = "High"
            elif risk_band == "Low" and app.status == "Under Validation":
                computed_priority = "Low"

            if priority and priority != "All" and computed_priority != priority:
                continue

            items.append({
                "id": app.id,
                "application_identifier": app.application_identifier,
                "institution_id": app.institution_id,
                "institution_name": app.institution.name if app.institution else None,
                "institution_city": app.institution.city if app.institution else None,
                "institution_state": app.institution.state if app.institution else None,
                "application_category": app.application_category,
                "academic_year": app.academic_year,
                "status": app.status,
                "submission_date": app.submission_date,
                "created_at": app.created_at,
                "assigned_reviewer_id": app.assigned_reviewer_id,
                "assigned_reviewer_name": app.assigned_reviewer.name if app.assigned_reviewer else None,
                "risk_band": risk_band,
                "risk_score": risk_score,
                "priority": computed_priority,
                "documents_count": len(app.documents) if app.documents else 0,
                "findings_count": len(app.findings) if app.findings else 0,
            })

        return items, total


class AuditService:
    @staticmethod
    def get_audit_events(
        db: Session,
        page: int = 1,
        limit: int = 25,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        query = db.query(AuditEvent)

        if entity_type and entity_type != "All":
            query = query.filter(AuditEvent.entity_type == entity_type)
        if action and action != "All":
            query = query.filter(AuditEvent.action.ilike(f"%{action}%"))
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    AuditEvent.entity_id.ilike(term),
                    AuditEvent.action.ilike(term),
                    AuditEvent.entity_type.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * limit
        events = query.order_by(desc(AuditEvent.created_at)).offset(offset).limit(limit).all()

        items = []
        for e in events:
            items.append({
                "id": e.id,
                "user_id": e.user_id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "action": e.action,
                "details": e.details or {},
                "created_at": e.created_at,
            })
        return items, total


class AnalyticsService:
    @staticmethod
    def get_analytics(db: Session) -> dict:
        total_apps = db.query(func.count(Application.id)).scalar() or 0
        total_insts = db.query(func.count(Institution.id)).scalar() or 0
        total_docs = db.query(func.count(Document.id)).scalar() or 0
        total_findings = db.query(func.count(Finding.id)).scalar() or 0

        status_counts = (
            db.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )
        status_breakdown = {s: count for s, count in status_counts}

        cat_counts = (
            db.query(Application.application_category, func.count(Application.id))
            .group_by(Application.application_category)
            .all()
        )
        category_breakdown = {c: count for c, count in cat_counts}

        inst_counts = (
            db.query(Institution.institution_type, func.count(Institution.id))
            .group_by(Institution.institution_type)
            .all()
        )
        institution_type_breakdown = {t: count for t, count in inst_counts}

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
        risk_breakdown = {"Low": 0, "Medium": 0, "High": 0, "Extreme": 0}
        for band, count in latest_risks:
            if band:
                risk_breakdown[band] = count

        finding_counts = (
            db.query(Finding.severity, func.count(Finding.id))
            .group_by(Finding.severity)
            .all()
        )
        findings_by_severity = {sev: count for sev, count in finding_counts}

        doc_counts = (
            db.query(Document.processing_status, func.count(Document.id))
            .group_by(Document.processing_status)
            .all()
        )
        document_status_breakdown = {st: count for st, count in doc_counts}

        state_counts = (
            db.query(Institution.state, func.count(Application.id))
            .join(Application, Application.institution_id == Institution.id)
            .group_by(Institution.state)
            .order_by(desc(func.count(Application.id)))
            .limit(8)
            .all()
        )
        state_distribution = {state: count for state, count in state_counts}

        recent_events = (
            db.query(AuditEvent)
            .order_by(desc(AuditEvent.created_at))
            .limit(8)
            .all()
        )
        recent_activity = [
            {
                "id": ev.id,
                "entity_type": ev.entity_type,
                "entity_id": ev.entity_id,
                "action": ev.action,
                "details": ev.details or {},
                "created_at": ev.created_at,
            }
            for ev in recent_events
        ]

        return {
            "total_applications": total_apps,
            "total_institutions": total_insts,
            "total_documents": total_docs,
            "total_findings": total_findings,
            "status_breakdown": status_breakdown,
            "category_breakdown": category_breakdown,
            "institution_type_breakdown": institution_type_breakdown,
            "risk_breakdown": risk_breakdown,
            "findings_by_severity": findings_by_severity,
            "document_status_breakdown": document_status_breakdown,
            "state_distribution": state_distribution,
            "recent_activity": recent_activity,
        }


class SystemService:
    @staticmethod
    def get_system_info(db: Session) -> dict:
        from app.core.config import settings
        db_connected = True
        try:
            db.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception:
            db_connected = False

        total_apps = db.query(func.count(Application.id)).scalar() or 0
        total_insts = db.query(func.count(Institution.id)).scalar() or 0

        return {
            "system": {
                "project_name": settings.PROJECT_NAME,
                "environment": settings.ENVIRONMENT,
                "version": "1.0.0",
                "handbook_edition": "APH 2026-2027",
                "storage_type": settings.STORAGE_TYPE,
                "database_engine": "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite",
                "database_connected": db_connected,
                "total_persisted_applications": total_apps,
                "total_persisted_institutions": total_insts,
            },
            "officer_profile": {
                "name": "AICTE Scrutiny Officer",
                "designation": "Assistant Director / Scrutiny Member",
                "bureau": "Approval Bureau (AICTE Central Office)",
                "email": "scrutiny.officer@aicte-india.org",
                "assigned_region": "National Master (All Regions)",
                "role": "Scrutiny Officer / Reviewer",
                "permissions": [
                    "READ_APPLICATIONS",
                    "WRITE_REVIEWS",
                    "EVALUATE_COMPLIANCE",
                    "GENERATE_RISK_SCORES",
                    "INSPECT_SECURE_DOCUMENTS",
                    "VIEW_AUDIT_LOGS",
                ],
            },
            "security_status": {
                "document_authorization": "Enforced (Bearer & Signed Auth Token)",
                "integrity_checks": "SHA-256 Cryptographic Hash Verification Active",
                "audit_immutability": "Strict Append-Only",
                "sso_two_factor": "Managed by AICTE Central IT (Disabled in current deployment)",
                "biometric_auth": "Unimplemented (Planned for hardware token rollout)",
            },
        }

