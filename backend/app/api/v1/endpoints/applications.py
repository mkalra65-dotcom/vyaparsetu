from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.models.application import Application
from app.models.document import Document
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.schemas.document import DocumentRead
from app.services.application_workflow import (
    get_missing_required_documents,
    get_required_documents,
    sync_document_status,
)
from app.services.audit import add_application_audit_log
from app.services.document_storage import (
    build_upload_path,
    validate_file_size,
    validate_upload_metadata,
)
from app.services.document_intelligence import process_document_extraction
from app.services.notification_service import notify_admin, notify_application_event

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
    file_size = len(content)
    validate_file_size(file_size)

    original_filename = file.filename or "upload"
    file_path, stored_filename = build_upload_path(application_id, original_filename)
    file_path.write_bytes(content)

    document = Document(
        application=application,
        document_type=document_type,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        uploaded_by_user_id=current_user.id,
    )
    old_status = application.status
    db.add(document)
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
    notify_application_event(db, application, "document_uploaded")
    if old_status != application.status:
        notify_application_event(db, application, application.status)
    db.commit()
    db.refresh(document)
    background_tasks.add_task(process_document_extraction, document.id)
    return document
