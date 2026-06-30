from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.application import Application
from app.models.document import Document
from app.models.enums import ApplicationStatus, ServiceType
from app.models.user import User
from app.models.whatsapp import ConversationMessage, ConversationSession, WhatsAppContact
from app.services.application_workflow import get_missing_required_documents, sync_document_status
from app.services.audit import add_application_audit_log
from app.services.document_storage import store_document_bytes, validate_file_metadata
from app.services.notification_service import notify_application_event
from app.services.timeline import add_timeline_event, find_open_query_for_document, mark_query_responded
from app.services.whatsapp.base import WhatsAppMediaRequest, WhatsAppSendRequest
from app.services.whatsapp.provider_factory import get_whatsapp_provider

SERVICE_SELECTIONS: dict[str, ServiceType] = {
    "1": ServiceType.GST_REGISTRATION,
    "gst": ServiceType.GST_REGISTRATION,
    "gst registration": ServiceType.GST_REGISTRATION,
    "2": ServiceType.FSSAI_REGISTRATION,
    "fssai": ServiceType.FSSAI_REGISTRATION,
    "fssai registration": ServiceType.FSSAI_REGISTRATION,
    "3": ServiceType.UDYAM_REGISTRATION,
    "udyam": ServiceType.UDYAM_REGISTRATION,
    "udyam registration": ServiceType.UDYAM_REGISTRATION,
}

SERVICE_LABELS = {
    ServiceType.GST_REGISTRATION: "GST Registration",
    ServiceType.FSSAI_REGISTRATION: "FSSAI Registration",
    ServiceType.UDYAM_REGISTRATION: "Udyam Registration",
}

MENU_MESSAGE = (
    "Hi, welcome to VyaparSetu. Which registration do you need?\n"
    "1. GST Registration\n"
    "2. FSSAI Registration\n"
    "3. Udyam Registration\n"
    "Reply with 1, 2, 3, GST, FSSAI, or Udyam."
)

DOCUMENT_TYPE_ALIASES = {
    "aadhaar": "aadhaar_card",
    "aadhar": "aadhaar_card",
    "aadhaar card": "aadhaar_card",
    "aadhar card": "aadhaar_card",
    "pan": "pan_card",
    "pan card": "pan_card",
    "pan_card": "pan_card",
    "business address proof": "business_address_proof",
    "address proof": "business_address_proof",
    "bank proof": "bank_account_proof",
    "bank account proof": "bank_account_proof",
    "photo id": "photo_id",
    "photo_id": "photo_id",
    "food business address proof": "food_business_address_proof",
    "food safety management plan": "food_safety_management_plan",
}

MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def normalize_phone_number(value: str) -> str:
    normalized = "".join(character for character in value.strip() if character.isdigit() or character == "+")
    return normalized or value.strip()


def get_or_create_contact(
    db: Session,
    *,
    phone_number: str,
    wa_id: str | None,
    display_name: str | None,
) -> WhatsAppContact:
    normalized_phone = normalize_phone_number(phone_number)
    contact = (
        db.query(WhatsAppContact)
        .filter(WhatsAppContact.phone_number == normalized_phone)
        .first()
    )
    if contact is None and wa_id:
        contact = db.query(WhatsAppContact).filter(WhatsAppContact.wa_id == wa_id).first()
    if contact is None:
        contact = WhatsAppContact(
            phone_number=normalized_phone,
            wa_id=wa_id,
            display_name=display_name,
            consent_status="inbound_opt_in",
        )
        db.add(contact)
        db.flush()
    else:
        if wa_id and contact.wa_id != wa_id:
            contact.wa_id = wa_id
        if display_name and contact.display_name != display_name:
            contact.display_name = display_name
        contact.consent_status = "inbound_opt_in"
        db.add(contact)
    return contact


def get_or_create_contact_user(db: Session, contact: WhatsAppContact) -> User:
    if contact.user_id is not None:
        user = db.get(User, contact.user_id)
        if user is not None:
            return user

    phone_key = "".join(character for character in contact.phone_number if character.isdigit())
    email = f"whatsapp-{phone_key or contact.id}@whatsapp.vyaparsetu.local"
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            full_name=contact.display_name or f"WhatsApp Customer {contact.phone_number}",
            hashed_password=get_password_hash(uuid4().hex),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        db.flush()
    contact.user_id = user.id
    db.add(contact)
    return user


def get_or_create_session(db: Session, contact: WhatsAppContact) -> ConversationSession:
    session = (
        db.query(ConversationSession)
        .filter(ConversationSession.contact_id == contact.id)
        .order_by(ConversationSession.created_at.desc())
        .first()
    )
    if session is None:
        session = ConversationSession(
            contact_id=contact.id,
            state="awaiting_service_selection",
            last_message_at=datetime.now(UTC),
        )
        db.add(session)
        db.flush()
    return session


def store_message(
    db: Session,
    *,
    contact: WhatsAppContact,
    session: ConversationSession | None,
    direction: str,
    message_type: str,
    body: str | None,
    provider: str = "whatsapp",
    provider_message_id: str | None = None,
    status: str = "received",
    raw_payload: dict | None = None,
) -> ConversationMessage:
    message = ConversationMessage(
        contact_id=contact.id,
        session_id=session.id if session else None,
        application_id=session.application_id if session else None,
        direction=direction,
        message_type=message_type,
        body=body,
        provider=provider,
        provider_message_id=provider_message_id,
        status=status,
        raw_payload=raw_payload,
    )
    db.add(message)
    db.flush()
    return message


def _normalize_document_type(value: str | None) -> str | None:
    if not value:
        return None
    normalized = Path(value).stem.replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.lower().split())
    if normalized in DOCUMENT_TYPE_ALIASES:
        return DOCUMENT_TYPE_ALIASES[normalized]
    for label, document_type in DOCUMENT_TYPE_ALIASES.items():
        if label in normalized:
            return document_type
    return None


def _resolve_document_type(application: Application, caption: str | None, filename: str | None) -> str:
    document_type = _normalize_document_type(caption) or _normalize_document_type(filename)
    if document_type is not None:
        return document_type
    missing_documents = get_missing_required_documents(application)
    if missing_documents:
        return missing_documents[0]
    return "whatsapp_document"


def _build_media_filename(
    *,
    provider_media_id: str,
    message_type: str,
    mime_type: str,
    filename: str | None,
) -> str:
    if filename:
        return filename
    suffix = MIME_EXTENSIONS.get(mime_type, "")
    return f"whatsapp-{message_type}-{provider_media_id}{suffix}"


def send_and_store_message(
    db: Session,
    *,
    contact: WhatsAppContact,
    session: ConversationSession,
    message: str,
) -> ConversationMessage:
    provider = get_whatsapp_provider()
    result = provider.send_text(
        WhatsAppSendRequest(
            recipient=contact.phone_number,
            message=message,
        )
    )
    return store_message(
        db,
        contact=contact,
        session=session,
        direction="outbound",
        message_type="text",
        body=message,
        provider=provider.provider_name,
        provider_message_id=result.provider_message_id,
        status=result.status,
        raw_payload={"error_message": result.error_message} if result.error_message else None,
    )


def parse_service_selection(message_body: str) -> ServiceType | None:
    normalized = " ".join(message_body.strip().lower().split())
    return SERVICE_SELECTIONS.get(normalized)


def create_draft_application(
    db: Session,
    *,
    contact: WhatsAppContact,
    session: ConversationSession,
    service_type: ServiceType,
) -> Application:
    if session.application_id is not None:
        application = db.get(Application, session.application_id)
        if application is not None:
            return application

    user = get_or_create_contact_user(db, contact)
    label = SERVICE_LABELS[service_type]
    application = Application(
        title=f"WhatsApp {label}",
        description="Created from WhatsApp conversation intake.",
        service_type=service_type.value,
        status=ApplicationStatus.DRAFT.value,
        business_name=f"WhatsApp intake {contact.phone_number}",
        applicant_mobile=contact.phone_number,
        applicant_email=user.email,
        owner_id=user.id,
    )
    db.add(application)
    db.flush()
    session.application_id = application.id
    session.selected_service_type = service_type.value
    session.state = "draft_application_created"
    session.last_message_at = datetime.now(UTC)
    db.add(session)
    add_timeline_event(
        db,
        application=application,
        event_type="application_created",
        actor_user_id=user.id,
        source_channel="whatsapp",
    )
    return application


def handle_text_message(
    db: Session,
    *,
    phone_number: str,
    wa_id: str | None,
    display_name: str | None,
    provider_message_id: str | None,
    message_body: str,
    raw_payload: dict,
) -> ConversationSession:
    if provider_message_id:
        existing_message = (
            db.query(ConversationMessage)
            .filter(
                ConversationMessage.direction == "inbound",
                ConversationMessage.provider_message_id == provider_message_id,
            )
            .first()
        )
        if existing_message and existing_message.session_id:
            session = db.get(ConversationSession, existing_message.session_id)
            if session is not None:
                return session

    contact = get_or_create_contact(
        db,
        phone_number=phone_number,
        wa_id=wa_id,
        display_name=display_name,
    )
    session = get_or_create_session(db, contact)
    session.last_message_at = datetime.now(UTC)
    db.add(session)

    inbound_message = store_message(
        db,
        contact=contact,
        session=session,
        direction="inbound",
        message_type="text",
        body=message_body,
        provider_message_id=provider_message_id,
        raw_payload=raw_payload,
    )

    service_type = parse_service_selection(message_body)
    if service_type is None:
        session.state = "awaiting_service_selection"
        send_and_store_message(db, contact=contact, session=session, message=MENU_MESSAGE)
        return session

    application = create_draft_application(
        db,
        contact=contact,
        session=session,
        service_type=service_type,
    )
    inbound_message.application_id = application.id
    db.add(inbound_message)
    label = SERVICE_LABELS[service_type]
    send_and_store_message(
        db,
        contact=contact,
        session=session,
        message=(
            f"Great. I created draft application #{application.id} for {label}. "
            "Next, our WhatsApp concierge will collect your details and documents."
        ),
    )
    return session


def handle_media_message(
    db: Session,
    *,
    phone_number: str,
    wa_id: str | None,
    display_name: str | None,
    provider_message_id: str | None,
    message_type: str,
    media_payload: dict,
    raw_payload: dict,
) -> ConversationSession:
    if provider_message_id:
        existing_message = (
            db.query(ConversationMessage)
            .filter(
                ConversationMessage.direction == "inbound",
                ConversationMessage.provider_message_id == provider_message_id,
            )
            .first()
        )
        if existing_message and existing_message.session_id:
            session = db.get(ConversationSession, existing_message.session_id)
            if session is not None:
                return session

    contact = get_or_create_contact(
        db,
        phone_number=phone_number,
        wa_id=wa_id,
        display_name=display_name,
    )
    session = get_or_create_session(db, contact)
    session.last_message_at = datetime.now(UTC)
    db.add(session)

    caption = media_payload.get("caption")
    inbound_message = store_message(
        db,
        contact=contact,
        session=session,
        direction="inbound",
        message_type=message_type,
        body=caption,
        provider_message_id=provider_message_id,
        raw_payload=raw_payload,
    )

    if session.application_id is None:
        session.state = "awaiting_service_selection"
        send_and_store_message(
            db,
            contact=contact,
            session=session,
            message=(
                "I received your document. Please choose the registration first so I can attach it correctly.\n"
                f"{MENU_MESSAGE}"
            ),
        )
        return session

    application = db.get(Application, session.application_id)
    if application is None:
        session.application_id = None
        session.state = "awaiting_service_selection"
        send_and_store_message(
            db,
            contact=contact,
            session=session,
            message=f"I could not find an active application. {MENU_MESSAGE}",
        )
        return session

    provider_media_id = media_payload.get("id")
    if not provider_media_id:
        inbound_message.status = "failed"
        send_and_store_message(
            db,
            contact=contact,
            session=session,
            message="I could not read that document upload. Please send the file again.",
        )
        return session

    try:
        provider = get_whatsapp_provider()
        media = provider.download_media(WhatsAppMediaRequest(provider_media_id=provider_media_id))
        original_filename = _build_media_filename(
            provider_media_id=provider_media_id,
            message_type=message_type,
            mime_type=media.mime_type,
            filename=media.filename or media_payload.get("filename"),
        )
        validate_file_metadata(original_filename, media.mime_type)
        file_path, stored_filename, file_size = store_document_bytes(application.id, original_filename, media.content)
    except (FileNotFoundError, HTTPException) as exc:
        inbound_message.status = "failed"
        inbound_message.raw_payload = {
            **(inbound_message.raw_payload or {}),
            "provider_media_id": provider_media_id,
            "error": str(getattr(exc, "detail", exc)),
        }
        db.add(inbound_message)
        send_and_store_message(
            db,
            contact=contact,
            session=session,
            message="I could not store that document. Please send a PDF, JPG, JPEG, or PNG file under 10MB.",
        )
        return session
    document_type = _resolve_document_type(application, caption, original_filename)

    old_status = application.status
    document = Document(
        application=application,
        document_type=document_type,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type=media.mime_type,
        file_size=file_size,
        provider_media_id=provider_media_id,
        source_channel="whatsapp",
        uploaded_by_user_id=application.owner_id,
    )
    db.add(document)
    db.flush()

    inbound_message.application_id = application.id
    inbound_message.raw_payload = {
        **(inbound_message.raw_payload or {}),
        "document_id": document.id,
        "provider_media_id": provider_media_id,
    }
    db.add(inbound_message)

    sync_document_status(application)
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=application.owner_id,
        action="document_uploaded",
        old_status=old_status,
        new_status=application.status,
        note=f"WhatsApp uploaded {document_type}: {original_filename}",
    )
    add_timeline_event(
        db,
        application=application,
        event_type="document_uploaded",
        actor_user_id=application.owner_id,
        source_channel="whatsapp",
        metadata={"document_id": document.id, "document_type": document_type, "detail": document_type.replace("_", " ")},
    )
    open_query = find_open_query_for_document(application, document_type)
    if open_query is not None:
        mark_query_responded(
            db,
            query=open_query,
            document_id=document.id,
            actor_user_id=application.owner_id,
            source_channel="whatsapp",
        )
        add_application_audit_log(
            db,
            application_id=application.id,
            actor_user_id=application.owner_id,
            action="government_query_responded",
            old_status=application.status,
            new_status=application.status,
            note=f"WhatsApp response to query #{open_query.id} with {document_type}",
        )
    notify_application_event(db, application, "document_uploaded")
    if old_status != application.status:
        notify_application_event(db, application, application.status)

    session.state = "document_received"
    send_and_store_message(
        db,
        contact=contact,
        session=session,
        message=f"Received {document_type.replace('_', ' ')}. Please send any remaining required documents.",
    )
    return session
