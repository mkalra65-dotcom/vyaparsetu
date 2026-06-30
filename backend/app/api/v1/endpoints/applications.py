from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.application import Application
from app.models.certificate import Certificate
from app.models.document import Document
from app.models.feedback import CustomerFeedback
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.schemas.certificate import CertificateRead, FeedbackCreate, FeedbackRead
from app.schemas.document import DocumentRead
from app.schemas.tracking import ApplicationTrackingRead
from app.services.application_workflow import (
    get_missing_required_documents,
    get_required_documents,
    sync_document_status,
)
from app.services.audit import add_application_audit_log
from app.services.document_storage import (
    store_document_bytes,
    validate_upload_metadata,
)
from app.services.document_intelligence import process_document_extraction
from app.services.notification_service import notify_admin, notify_application_event
from app.services.timeline import add_timeline_event, find_open_query_for_document, mark_query_responded

router = APIRouter()


def get_accessible_application(
    application_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if not current_user.is_admin and application.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return application


def serialize_application(application: Application, viewer: User) -> dict:
    return {
        "id": application.id,
        "title": application.title,
        "description": application.description,
        "service_type": application.service_type,
        "status": application.status,
        "business_name": application.business_name,
        "proprietor_name": application.proprietor_name,
        "applicant_mobile": application.applicant_mobile,
        "applicant_email": application.applicant_email,
        "pan_number": application.pan_number,
        "aadhaar_number": application.aadhaar_number,
        "business_address": application.business_address,
        "city": application.city,
        "pincode": application.pincode,
        "state": application.state,
        "business_type": application.business_type,
        "business_constitution": application.business_constitution,
        "nature_of_business": application.nature_of_business,
        "principal_place_of_business": application.principal_place_of_business,
        "bank_account_details": application.bank_account_details,
        "expected_turnover": application.expected_turnover,
        "annual_turnover": application.annual_turnover,
        "food_business_type": application.food_business_type,
        "food_category": application.food_category,
        "premises_address": application.premises_address,
        "license_type_suggestion": application.license_type_suggestion,
        "fssai_license_category": application.fssai_license_category,
        "enterprise_name": application.enterprise_name,
        "type_of_organisation": application.type_of_organisation,
        "major_activity": application.major_activity,
        "nic_code": application.nic_code,
        "enterprise_type": application.enterprise_type,
        "investment_amount": application.investment_amount,
        "turnover": application.turnover,
        "customer_clarification_message": application.customer_clarification_message,
        "internal_admin_notes": application.internal_admin_notes if viewer.is_admin else None,
        "health_score": application.health_score if viewer.is_admin else None,
        "ai_review_summary": application.ai_review_summary if viewer.is_admin else None,
        "required_documents": sorted(get_required_documents(application.service_type)),
        "missing_required_documents": get_missing_required_documents(application),
        "owner_id": application.owner_id,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
    }


@router.get("", response_model=list[ApplicationRead])
def list_applications(db: DbSession, current_user: CurrentUser) -> list[dict]:
    if current_user.is_admin:
        applications = db.query(Application).order_by(Application.created_at.desc()).all()
    else:
        applications = (
            db.query(Application)
            .filter(Application.owner_id == current_user.id)
            .order_by(Application.created_at.desc())
            .all()
        )
    return [serialize_application(application, current_user) for application in applications]


@router.get("/my", response_model=list[ApplicationRead])
def list_my_applications(db: DbSession, current_user: CurrentUser) -> list[dict]:
    applications = (
        db.query(Application)
        .filter(Application.owner_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return [serialize_application(application, current_user) for application in applications]


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    application_in: ApplicationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    application = Application(
        title=application_in.title,
        description=application_in.description,
        service_type=application_in.service_type.value,
        business_name=application_in.business_name,
        proprietor_name=application_in.proprietor_name,
        applicant_mobile=application_in.applicant_mobile,
        applicant_email=application_in.applicant_email,
        pan_number=application_in.pan_number,
        aadhaar_number=application_in.aadhaar_number,
        business_address=application_in.business_address,
        city=application_in.city,
        pincode=application_in.pincode,
        state=application_in.state,
        business_type=application_in.business_type,
        business_constitution=application_in.business_constitution,
        nature_of_business=application_in.nature_of_business,
        principal_place_of_business=application_in.principal_place_of_business,
        bank_account_details=application_in.bank_account_details,
        expected_turnover=application_in.expected_turnover,
        annual_turnover=application_in.annual_turnover,
        food_business_type=application_in.food_business_type,
        food_category=application_in.food_category,
        premises_address=application_in.premises_address,
        license_type_suggestion=application_in.license_type_suggestion,
        fssai_license_category=application_in.fssai_license_category,
        enterprise_name=application_in.enterprise_name,
        type_of_organisation=application_in.type_of_organisation,
        major_activity=application_in.major_activity,
        nic_code=application_in.nic_code,
        enterprise_type=application_in.enterprise_type,
        investment_amount=application_in.investment_amount,
        turnover=application_in.turnover,
        owner_id=current_user.id,
    )
    sync_document_status(application)
    db.add(application)
    db.flush()
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=current_user.id,
        action="application_created",
        old_status=None,
        new_status=application.status,
        note="Application created",
    )
    add_timeline_event(
        db,
        application=application,
        event_type="application_created",
        actor_user_id=current_user.id,
        source_channel="web",
    )
    notify_application_event(db, application, "application_created")
    if application.status == "documents_pending":
        notify_application_event(db, application, "documents_pending")
    db.commit()
    db.refresh(application)
    return serialize_application(application, current_user)


@router.get("/{application_id}", response_model=ApplicationRead)
def read_application(
    application_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    application = get_accessible_application(application_id, db, current_user)
    return serialize_application(application, current_user)


@router.get("/{application_id}/tracking", response_model=ApplicationTrackingRead)
def read_application_tracking(
    application_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    application = get_accessible_application(application_id, db, current_user)
    return {
        "application": serialize_application(application, current_user),
        "timeline_events": sorted(application.timeline_events, key=lambda event: event.created_at, reverse=True),
        "government_queries": sorted(application.government_queries, key=lambda query: query.created_at, reverse=True),
        "documents": sorted(application.documents, key=lambda document: document.created_at, reverse=True),
        "certificates": sorted(application.certificates, key=lambda certificate: certificate.uploaded_at, reverse=True),
        "feedback": sorted(application.feedback_entries, key=lambda feedback: feedback.created_at, reverse=True),
    }


def get_accessible_certificate(
    certificate_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Certificate:
    certificate = db.get(Certificate, certificate_id)
    if certificate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    if not current_user.is_admin and certificate.application.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return certificate


@router.get("/{application_id}/certificates", response_model=list[CertificateRead])
def list_application_certificates(
    application_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[Certificate]:
    application = get_accessible_application(application_id, db, current_user)
    return sorted(application.certificates, key=lambda certificate: certificate.uploaded_at, reverse=True)


@router.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> FileResponse:
    certificate = get_accessible_certificate(certificate_id, db, current_user)
    return FileResponse(
        certificate.file_path,
        media_type=certificate.mime_type,
        filename=certificate.original_filename,
    )


@router.post("/{application_id}/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def submit_application_feedback(
    application_id: int,
    feedback_in: FeedbackCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> CustomerFeedback:
    application = get_accessible_application(application_id, db, current_user)
    feedback = CustomerFeedback(
        application_id=application.id,
        user_id=current_user.id,
        rating=feedback_in.rating,
        feedback=feedback_in.feedback,
    )
    db.add(feedback)
    db.flush()
    add_timeline_event(
        db,
        application=application,
        event_type="feedback_received",
        actor_user_id=current_user.id,
        source_channel="web",
        metadata={"rating": feedback.rating, "feedback_id": feedback.id},
        send_whatsapp=False,
    )
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=current_user.id,
        action="feedback_submitted",
        old_status=application.status,
        new_status=application.status,
        note=f"Rating {feedback.rating}",
    )
    db.commit()
    db.refresh(feedback)
    return feedback


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    application_in: ApplicationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    application = get_accessible_application(application_id, db, current_user)
    old_status = application.status
    update_data = application_in.model_dump(exclude_unset=True)

    if not current_user.is_admin:
        update_data.pop("status", None)
        update_data.pop("customer_clarification_message", None)
        update_data.pop("internal_admin_notes", None)

    for field_name, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(application, field_name, value)

    sync_document_status(application)
    if not current_user.is_admin and old_status == "clarification_required":
        notify_admin(db, application, "clarification_required")
    db.add(application)
    db.commit()
    db.refresh(application)
    return serialize_application(application, current_user)


@router.get("/{application_id}/documents", response_model=list[DocumentRead])
def list_application_documents(
    application_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[Document]:
    application = get_accessible_application(application_id, db, current_user)
    return sorted(application.documents, key=lambda document: document.created_at, reverse=True)


@router.post(
    "/{application_id}/documents/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_application_document(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
    document_type: str = Form(min_length=1, max_length=100),
    file: UploadFile = File(),
) -> Document:
    application = get_accessible_application(application_id, db, current_user)
    validate_upload_metadata(file)

    content = await file.read()

    original_filename = file.filename or "upload"
    file_path, stored_filename, file_size = store_document_bytes(application_id, original_filename, content)

    document = Document(
        application=application,
        document_type=document_type,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        source_channel="web",
        uploaded_by_user_id=current_user.id,
    )
    old_status = application.status
    db.add(document)
    db.flush()
    sync_document_status(application)
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=current_user.id,
        action="document_uploaded",
        old_status=old_status,
        new_status=application.status,
        note=f"Uploaded {document_type}: {original_filename}",
    )
    add_timeline_event(
        db,
        application=application,
        event_type="document_uploaded",
        actor_user_id=current_user.id,
        source_channel="web",
        metadata={"document_id": document.id, "document_type": document_type, "detail": document_type.replace("_", " ")},
    )
    open_query = find_open_query_for_document(application, document_type)
    if open_query is not None:
        mark_query_responded(
            db,
            query=open_query,
            document_id=document.id,
            actor_user_id=current_user.id,
            source_channel="web",
        )
        add_application_audit_log(
            db,
            application_id=application.id,
            actor_user_id=current_user.id,
            action="government_query_responded",
            old_status=application.status,
            new_status=application.status,
            note=f"Responded to query #{open_query.id} with {document_type}",
        )
    notify_application_event(db, application, "document_uploaded")
    if old_status != application.status:
        notify_application_event(db, application, application.status)
    db.commit()
    db.refresh(document)
    if settings.DOCUMENT_INTELLIGENCE_ENABLED:
        background_tasks.add_task(process_document_extraction, document.id)
    return document
