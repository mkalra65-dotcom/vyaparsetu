from datetime import UTC, datetime

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy import func

from app.api.deps import AdminUser, DbSession
from app.api.v1.endpoints.applications import serialize_application
from app.models.application import Application
from app.models.certificate import Certificate
from app.models.enums import ApplicationStatus, ServiceType
from app.models.feedback import CustomerFeedback
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
from app.schemas.tracking import (
    GovernmentQueryCreate,
    GovernmentQueryRead,
    TimelineEventCreate,
)
from app.schemas.certificate import FeedbackRead
from app.services.application_workflow import get_missing_required_documents
from app.services.audit import add_application_audit_log
from app.services.notification_service import notify_application_event
from app.services.document_storage import store_document_bytes, validate_upload_metadata
from app.services.timeline import (
    add_timeline_event,
    create_government_query,
    create_overdue_alerts,
    send_whatsapp_timeline_update,
)

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
            "provider_media_id": document.provider_media_id,
            "source_channel": document.source_channel,
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
    data["certificates"] = sorted(
        application.certificates,
        key=lambda certificate: certificate.uploaded_at,
        reverse=True,
    )
    data["feedback"] = sorted(
        application.feedback_entries,
        key=lambda feedback: feedback.created_at,
        reverse=True,
    )
    data["timeline_events"] = sorted(
        application.timeline_events,
        key=lambda timeline_event: timeline_event.created_at,
        reverse=True,
    )
    data["government_queries"] = sorted(
        application.government_queries,
        key=lambda query: query.created_at,
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


@router.get("/feedback", response_model=list[FeedbackRead])
def list_customer_feedback(db: DbSession, _: AdminUser) -> list[CustomerFeedback]:
    return db.query(CustomerFeedback).order_by(CustomerFeedback.created_at.desc()).limit(100).all()


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
    timeline_event_type_by_status = {
        ApplicationStatus.UNDER_REVIEW.value: "review_started",
        ApplicationStatus.READY_FOR_FILING.value: "ready_for_filing",
        ApplicationStatus.FILING_IN_PROGRESS.value: "filing_in_progress",
        ApplicationStatus.FILED.value: "filing_submitted",
        ApplicationStatus.APPROVED.value: "application_approved",
        ApplicationStatus.REJECTED.value: "application_rejected",
        ApplicationStatus.CERTIFICATE_DELIVERED.value: "certificate_delivered",
        ApplicationStatus.COMPLETED.value: "application_completed",
    }
    timeline_event_type = timeline_event_type_by_status.get(application.status) if old_status != application.status else None
    if timeline_event_type is not None:
        add_timeline_event(
            db,
            application=application,
            event_type=timeline_event_type,
            actor_user_id=admin_user.id,
            source_channel="admin",
            description=status_in.note,
        )
    notify_application_event(db, application, application.status)
    db.add(application)
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)


@router.post("/applications/{application_id}/certificates/upload", response_model=AdminApplicationDetail)
async def upload_application_certificate(
    application_id: int,
    db: DbSession,
    admin_user: AdminUser,
    certificate_type: str = Form(min_length=1, max_length=100),
    file: UploadFile = File(),
) -> dict:
    allowed_certificate_types = {"gst_certificate", "fssai_certificate", "udyam_certificate"}
    if certificate_type not in allowed_certificate_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"certificate_type must be one of: {', '.join(sorted(allowed_certificate_types))}",
        )
    application = get_admin_application(application_id, db)
    validate_upload_metadata(file)
    content = await file.read()
    original_filename = file.filename or "certificate"
    file_path, stored_filename, file_size = store_document_bytes(application_id, original_filename, content)
    certificate = Certificate(
        application_id=application.id,
        certificate_type=certificate_type,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        uploaded_by=admin_user.id,
    )
    db.add(certificate)
    db.flush()
    add_timeline_event(
        db,
        application=application,
        event_type="certificate_uploaded",
        actor_user_id=admin_user.id,
        source_channel="admin",
        metadata={"certificate_id": certificate.id, "certificate_type": certificate_type},
    )
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=admin_user.id,
        action="certificate_uploaded",
        old_status=application.status,
        new_status=application.status,
        note=f"Uploaded {certificate_type}: {original_filename}",
    )
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)


@router.post("/certificates/{certificate_id}/deliver", response_model=AdminApplicationDetail)
def deliver_certificate(
    certificate_id: int,
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    certificate = db.get(Certificate, certificate_id)
    if certificate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    application = certificate.application
    old_status = application.status
    delivered_at = datetime.now(UTC)
    certificate.delivered_at = delivered_at
    application.status = ApplicationStatus.CERTIFICATE_DELIVERED.value
    db.add(certificate)
    db.add(application)
    service_label = {
        ServiceType.GST_REGISTRATION.value: "GST registration",
        ServiceType.FSSAI_REGISTRATION.value: "FSSAI registration",
        ServiceType.UDYAM_REGISTRATION.value: "Udyam registration",
    }.get(application.service_type, "registration")
    add_timeline_event(
        db,
        application=application,
        event_type="certificate_delivered",
        actor_user_id=admin_user.id,
        source_channel="admin",
        metadata={
            "certificate_id": certificate.id,
            "certificate_type": certificate.certificate_type,
            "service_label": service_label,
        },
        send_whatsapp=False,
    )
    send_whatsapp_timeline_update(
        db,
        application,
        "certificate_delivered",
        {
            "certificate_id": certificate.id,
            "certificate_type": certificate.certificate_type,
            "service_label": service_label,
        },
    )
    add_timeline_event(
        db,
        application=application,
        event_type="feedback_requested",
        actor_user_id=admin_user.id,
        source_channel="system",
        send_whatsapp=False,
    )
    send_whatsapp_timeline_update(db, application, "feedback_requested", {})
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=admin_user.id,
        action="certificate_delivered",
        old_status=old_status,
        new_status=application.status,
        note=f"Delivered certificate #{certificate.id}",
    )
    notify_application_event(db, application, "certificate_delivered")
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)


@router.post("/applications/{application_id}/timeline-events", response_model=AdminApplicationDetail)
def create_admin_timeline_event(
    application_id: int,
    event_in: TimelineEventCreate,
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    allowed_events = {"review_started", "filing_submitted", "certificate_delivered"}
    if event_in.event_type not in allowed_events:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Event type must be one of: {', '.join(sorted(allowed_events))}",
        )
    application = get_admin_application(application_id, db)
    add_timeline_event(
        db,
        application=application,
        event_type=event_in.event_type,
        actor_user_id=admin_user.id,
        title=event_in.title,
        description=event_in.description,
        source_channel="admin",
    )
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=admin_user.id,
        action=f"timeline_{event_in.event_type}",
        old_status=application.status,
        new_status=application.status,
        note=event_in.description or event_in.title,
    )
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)


@router.post("/applications/{application_id}/queries", response_model=AdminApplicationDetail)
def create_admin_government_query(
    application_id: int,
    query_in: GovernmentQueryCreate,
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    application = get_admin_application(application_id, db)
    query = create_government_query(
        db,
        application=application,
        admin_user_id=admin_user.id,
        message=query_in.message,
        required_document_type=query_in.required_document_type,
        due_date=query_in.due_date,
    )
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=admin_user.id,
        action="government_query_created",
        old_status=application.status,
        new_status=application.status,
        note=f"Query #{query.id}: {query.required_document_type} due {query.due_date.isoformat()}",
    )
    db.commit()
    db.refresh(application)
    return serialize_admin_application_detail(application, admin_user)


@router.get("/queries/overdue", response_model=list[GovernmentQueryRead])
def list_overdue_government_queries(db: DbSession, admin_user: AdminUser) -> list:
    overdue_queries = create_overdue_alerts(db)
    for query in overdue_queries:
        if query.overdue_alerted_at is not None:
            add_application_audit_log(
                db,
                application_id=query.application_id,
                actor_user_id=admin_user.id,
                action="government_query_overdue_alerted",
                old_status=query.application.status,
                new_status=query.application.status,
                note=f"Query #{query.id} overdue since {query.due_date.isoformat()}",
            )
    db.commit()
    return overdue_queries


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
