from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.application import Application
from app.models.enums import ApplicationStatus, ServiceType
from app.models.user import User
from app.models.whatsapp import ConversationMessage, ConversationSession, WhatsAppContact
from app.services.whatsapp.base import WhatsAppSendRequest
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
