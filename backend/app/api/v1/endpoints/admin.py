from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy import func

from app.api.deps import AdminUser, DbSession
from app.api.v1.endpoints.applications import serialize_application
from app.models.application import Application
from app.models.enums import ApplicationStatus, ServiceType
from app.models.lead import Lead
from app.models.user import User
from app.schemas.admin import (
    ADMIN_ALLOWED_STATUSES,
    AdminApplicationDetail,
    AdminApplicationListResponse,
    AdminNotesUpdate,
    AdminStatusUpdate,
)
from app.schemas.notification import NotificationRead
from app.schemas.lead import LeadRead, LeadUpdate
from app.services.application_workflow import get_missing_required_documents
from app.services.audit import add_application_audit_log
from app.services.notification_service import notify_application_event

router = APIRouter()


def get_admin_application(application_id: int, db: DbSession) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


def serialize_admin_application_detail(application: Application, admin_user: User) -> dict:
    data = serialize_application(application, admin_user)
    data["documents"] = [
        {
            "id": document.id,
            "application_id": document.application_id,
            "document_type": document.document_type,
            "original_filename": document.original_filename,
            "stored_filename": document.stored_filename,
            "file_path": document.file_path,
            "mime_type": document.mime_type,
            "file_size": document.file_size,
            "uploaded_by_user_id": document.uploaded_by_user_id,
            "ai_processing_status": document.ai_processing_status,
            "requires_attention": document.requires_attention,
            "created_at": document.created_at,
            "extractions": document.extractions,
        }
        for document in sorted(
            application.documents,
            key=lambda item: item.created_at,
            reverse=True,
        )
    ]
    data["audit_logs"] = sorted(
        application.audit_logs,
        key=lambda audit_log: audit_log.created_at,
        reverse=True,
    )
    data["missing_required_documents"] = get_missing_required_documents(application)
    return data


@router.get("/applications", response_model=AdminApplicationListResponse)
def list_admin_applications(
    db: DbSession,
    admin_user: AdminUser,
    service_type: ServiceType | None = None,
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1),
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    query = db.query(Application).join(User, Application.owner_id == User.id)

    if service_type is not None:
        query = query.filter(Application.service_type == service_type.value)
    if status_filter is not None:
        query = query.filter(Application.status == status_filter.value)
    if created_from is not None:
        query = query.filter(Application.created_at >= created_from)
    if created_to is not None:
        query = query.filter(Application.created_at <= created_to)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Application.proprietor_name.ilike(pattern),
                Application.applicant_mobile.ilike(pattern),
                Application.business_name.ilike(pattern),
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    total = query.count()
    applications = (
        query.order_by(Application.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_application(application, admin_user) for application in applications],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/applications/metrics")
def read_admin_application_metrics(db: DbSession, _: AdminUser) -> dict[str, int]:
    rows = db.query(Application.service_type, Application.status, func.count(Application.id)).group_by(
        Application.service_type,
        Application.status,
    )
    metrics = {
        "total_applications": 0,
        "gst_applications": 0,
        "fssai_applications": 0,
        "udyam_applications": 0,
        "documents_pending": 0,
        "under_review": 0,
        "clarification_required": 0,
        "approved": 0,
        "rejected": 0,
    }
    for service_type, application_status, count in rows:
        metrics["total_applications"] += count
        if service_type == ServiceType.GST_REGISTRATION.value:
            metrics["gst_applications"] += count
        elif service_type == ServiceType.FSSAI_REGISTRATION.value:
            metrics["fssai_applications"] += count
        elif service_type == ServiceType.UDYAM_REGISTRATION.value:
            metrics["udyam_applications"] += count

        if application_status in metrics:
            metrics[application_status] += count
    return metrics


@router.get("/notifications", response_model=list[NotificationRead])
def list_admin_notifications(db: DbSession, _: AdminUser) -> list:
    from app.models.notification import Notification

    return db.query(Notification).order_by(Notification.created_at.desc()).limit(100).all()


@router.get("/leads", response_model=list[LeadRead])
def list_admin_leads(db: DbSession, _: AdminUser) -> list[Lead]:
    return db.query(Lead).order_by(Lead.created_at.desc()).all()


@router.get("/leads/{lead_id}", response_model=LeadRead)
def read_admin_lead(lead_id: int, db: DbSession, _: AdminUser) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.patch("/leads/{lead_id}/status", response_model=LeadRead)
def update_admin_lead_status(
    lead_id: int,
    lead_in: LeadUpdate,
    db: DbSession,
    _: AdminUser,
) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    lead.status = lead_in.status.value
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/analytics")
def read_admin_analytics(db: DbSession, _: AdminUser) -> dict:
    total_leads = db.query(func.count(Lead.id)).scalar() or 0
    total_applications = db.query(func.count(Application.id)).scalar() or 0
    approved_applications = (
        db.query(func.count(Application.id))
        .filter(Application.status == ApplicationStatus.APPROVED.value)
        .scalar()
        or 0
    )
    conversion_rate = round((total_applications / total_leads) * 100, 2) if total_leads else 0
    service_rows = (
        db.query(Application.service_type, func.count(Application.id))
        .group_by(Application.service_type)
        .all()
    )
    return {
        "leads": total_leads,
        "applications": total_applications,
        "conversion_rate": conversion_rate,
        "applications_by_service": {service: count for service, count in service_rows},
        "approved_applications": approved_applications,
        "revenue_placeholder": "Configure billing before launch",
    }


@router.get("/applications/{application_id}", response_model=AdminApplicationDetail)
def read_admin_application_detail(
    application_id: int,
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    application = get_admin_application(application_id, db)
    return serialize_admin_application_detail(application, admin_user)


@router.patch("/applications/{application_id}/status", response_model=AdminApplicationDetail)
def update_admin_application_status(
    application_id: int,
    status_in: AdminStatusUpdate,
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    if status_in.status not in ADMIN_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status is not allowed for admin review",
        )

    application = get_admin_application(application_id, db)
    old_status = application.status
    application.status = status_in.status.value
    if status_in.customer_clarification_message is not None:
        application.customer_clarification_message = status_in.customer_clarification_message

    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=admin_user.id,
        action="admin_status_changed",
        old_status=old_status,
        new_status=application.status,
        note=status_in.note,
    )
    notify_application_event(db, application, application.status)
    db.add(application)
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)


@router.patch("/applications/{application_id}/notes", response_model=AdminApplicationDetail)
def update_admin_application_notes(
    application_id: int,
    notes_in: AdminNotesUpdate,
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    application = get_admin_application(application_id, db)
    update_data = notes_in.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(application, field_name, value)

    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=admin_user.id,
        action="admin_notes_updated",
        old_status=application.status,
        new_status=application.status,
        note="Admin notes or customer clarification message updated",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)
