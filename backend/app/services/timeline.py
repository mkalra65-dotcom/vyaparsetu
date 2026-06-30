from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_timeline import ApplicationTimelineEvent
from app.models.government_query import GovernmentQuery
from app.models.notification import Notification
from app.models.whatsapp import ConversationMessage, ConversationSession, WhatsAppContact
from app.services.notifications.base import NotificationSendRequest
from app.services.notifications.provider_factory import get_notification_provider
from app.services.whatsapp.base import WhatsAppSendRequest
from app.services.whatsapp.provider_factory import get_whatsapp_provider

TIMELINE_COPY = {
    "application_created": ("Application created", "Your application has been created."),
    "document_uploaded": ("Document uploaded", "A document has been received."),
    "review_started": ("Review started", "Your application review has started."),
    "filing_submitted": ("Filing submitted", "Your filing has been submitted."),
    "government_query_received": ("Government query received", "A government query needs your response."),
    "customer_response_received": ("Customer response received", "Your response has been received."),
    "application_approved": ("Application approved", "Your application has been approved."),
    "application_rejected": ("Application rejected", "Your application has been rejected."),
    "ready_for_filing": ("Ready for filing", "Your application is ready for filing."),
    "filing_in_progress": ("Filing in progress", "Your filing is in progress."),
    "certificate_uploaded": ("Certificate uploaded", "Your certificate is available in your account."),
    "certificate_delivered": ("Certificate delivered", "Your certificate has been delivered."),
    "application_completed": ("Application completed", "Your application lifecycle is complete."),
    "feedback_requested": ("Feedback requested", "We asked the customer to share feedback."),
    "feedback_received": ("Feedback received", "Thank you for sharing your experience."),
}

WHATSAPP_EVENT_MESSAGES = {
    "application_created": "VyaparSetu update: your application #{id} has been created.",
    "document_uploaded": "VyaparSetu update: we received {detail} for application #{id}.",
    "review_started": "VyaparSetu update: review has started for application #{id}.",
    "filing_submitted": "VyaparSetu update: filing has been submitted for application #{id}.",
    "government_query_received": "VyaparSetu update: a government query needs your response by {due_date}. Required document: {required_document_type}.",
    "customer_response_received": "VyaparSetu update: your response for application #{id} has been received.",
    "application_approved": "VyaparSetu update: application #{id} has been approved.",
    "application_rejected": "VyaparSetu update: application #{id} has been rejected. Please check your tracking page.",
    "ready_for_filing": "VyaparSetu update: application #{id} is ready for filing.",
    "filing_in_progress": "VyaparSetu update: filing is in progress for application #{id}.",
    "certificate_uploaded": "VyaparSetu update: your certificate for application #{id} is now available in your portal.",
    "certificate_delivered": (
        "Your {service_label} has been approved.\n\n"
        "Application ID: {id}\n\n"
        "Your certificate is now available.\n\n"
        "Thank you for choosing VyaparSetu."
    ),
    "application_completed": "VyaparSetu update: application #{id} has been completed.",
    "feedback_requested": "How was your experience with VyaparSetu?",
}


def _timeline_copy(event_type: str, title: str | None, description: str | None) -> tuple[str, str | None]:
    default_title, default_description = TIMELINE_COPY.get(event_type, (event_type.replace("_", " ").title(), None))
    return title or default_title, description if description is not None else default_description


def _find_application_contact(db: Session, application: Application) -> WhatsAppContact | None:
    contact = (
        db.query(WhatsAppContact)
        .filter(WhatsAppContact.user_id == application.owner_id)
        .order_by(WhatsAppContact.updated_at.desc())
        .first()
    )
    if contact is not None:
        return contact
    if not application.applicant_mobile:
        return None
    normalized_phone = "".join(
        character for character in application.applicant_mobile.strip() if character.isdigit() or character == "+"
    )
    return db.query(WhatsAppContact).filter(WhatsAppContact.phone_number == normalized_phone).first()


def _get_or_create_application_session(
    db: Session,
    contact: WhatsAppContact,
    application: Application,
) -> ConversationSession:
    session = (
        db.query(ConversationSession)
        .filter(
            ConversationSession.contact_id == contact.id,
            ConversationSession.application_id == application.id,
        )
        .order_by(ConversationSession.updated_at.desc())
        .first()
    )
    if session is None:
        session = ConversationSession(
            contact_id=contact.id,
            application_id=application.id,
            state="tracking_updates",
            selected_service_type=application.service_type,
            last_message_at=datetime.now(UTC),
        )
        db.add(session)
        db.flush()
    return session


def send_whatsapp_timeline_update(
    db: Session,
    application: Application,
    event_type: str,
    metadata: dict | None = None,
) -> ConversationMessage | None:
    template = WHATSAPP_EVENT_MESSAGES.get(event_type)
    if template is None:
        return None
    contact = _find_application_contact(db, application)
    if contact is None:
        return None
    session = _get_or_create_application_session(db, contact, application)
    template_data = {"id": application.id, "detail": "your document", "service_label": "registration"}
    template_data.update(metadata or {})
    message = template.format(**template_data)
    provider = get_whatsapp_provider()
    result = provider.send_text(WhatsAppSendRequest(recipient=contact.phone_number, message=message))
    outbound = ConversationMessage(
        contact_id=contact.id,
        session_id=session.id,
        application_id=application.id,
        direction="outbound",
        message_type="text",
        body=message,
        provider=provider.provider_name,
        provider_message_id=result.provider_message_id,
        status=result.status,
        raw_payload={"event_type": event_type, "error_message": result.error_message} if result.error_message else {"event_type": event_type},
    )
    session.last_message_at = datetime.now(UTC)
    db.add(outbound)
    db.add(session)
    db.flush()
    return outbound


def add_timeline_event(
    db: Session,
    *,
    application: Application,
    event_type: str,
    actor_user_id: int | None = None,
    title: str | None = None,
    description: str | None = None,
    source_channel: str = "system",
    metadata: dict | None = None,
    send_whatsapp: bool = True,
) -> ApplicationTimelineEvent:
    event_title, event_description = _timeline_copy(event_type, title, description)
    event = ApplicationTimelineEvent(
        application_id=application.id,
        event_type=event_type,
        title=event_title,
        description=event_description,
        actor_user_id=actor_user_id,
        source_channel=source_channel,
        metadata_json=metadata,
    )
    db.add(event)
    db.flush()
    if send_whatsapp:
        send_whatsapp_timeline_update(db, application, event_type, metadata)
    return event


def create_government_query(
    db: Session,
    *,
    application: Application,
    admin_user_id: int,
    message: str,
    required_document_type: str,
    due_date: date,
) -> GovernmentQuery:
    query = GovernmentQuery(
        application_id=application.id,
        raised_by_user_id=admin_user_id,
        message=message,
        required_document_type=required_document_type,
        due_date=due_date,
        status="open",
        sent_to_customer_at=datetime.now(UTC),
    )
    db.add(query)
    db.flush()
    add_timeline_event(
        db,
        application=application,
        event_type="government_query_received",
        actor_user_id=admin_user_id,
        source_channel="admin",
        description=message,
        metadata={
            "query_id": query.id,
            "required_document_type": required_document_type,
            "due_date": due_date.isoformat(),
        },
    )
    return query


def find_open_query_for_document(application: Application, document_type: str) -> GovernmentQuery | None:
    for query in application.government_queries:
        if query.status == "open" and query.required_document_type == document_type:
            return query
    return None


def mark_query_responded(
    db: Session,
    *,
    query: GovernmentQuery,
    document_id: int,
    actor_user_id: int,
    source_channel: str,
) -> GovernmentQuery:
    query.status = "responded"
    query.response_document_id = document_id
    query.responded_at = datetime.now(UTC)
    db.add(query)
    db.flush()
    add_timeline_event(
        db,
        application=query.application,
        event_type="customer_response_received",
        actor_user_id=actor_user_id,
        source_channel=source_channel,
        metadata={"query_id": query.id, "document_id": document_id, "required_document_type": query.required_document_type},
    )
    return query


def get_overdue_queries(db: Session) -> list[GovernmentQuery]:
    return (
        db.query(GovernmentQuery)
        .filter(GovernmentQuery.status == "open", GovernmentQuery.due_date < date.today())
        .order_by(GovernmentQuery.due_date.asc())
        .all()
    )


def create_overdue_alerts(db: Session) -> list[GovernmentQuery]:
    overdue_queries = get_overdue_queries(db)
    provider = get_notification_provider()
    for query in overdue_queries:
        if query.overdue_alerted_at is not None:
            continue
        application = query.application
        notification = Notification(
            user_id=None,
            application_id=application.id,
            channel="email",
            event_type="query_overdue",
            recipient="admin",
            subject="Government query overdue",
            message=(
                f"Query #{query.id} for application #{application.id} is overdue. "
                f"Required document: {query.required_document_type}."
            ),
            status="queued",
            provider=provider.provider_name,
        )
        db.add(notification)
        db.flush()
        result = provider.send(
            NotificationSendRequest(
                channel="email",
                recipient="admin",
                subject=notification.subject,
                message=notification.message,
            )
        )
        notification.status = result.status
        notification.provider_message_id = result.provider_message_id
        notification.error_message = result.error_message
        if result.status == "sent":
            notification.sent_at = datetime.now(UTC)
        query.overdue_alerted_at = datetime.now(UTC)
        db.add(notification)
        db.add(query)
    return overdue_queries
