from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.application import Application
from app.models.notification import Notification
from app.services.notifications.base import NotificationSendRequest
from app.services.notifications.provider_factory import get_notification_provider

CUSTOMER_MESSAGES = {
    "application_created": (
        "Application created",
        "Your VyaparSetu application has been created. Upload your documents to continue.",
    ),
    "documents_pending": (
        "Documents missing",
        "Some required documents are still missing. Please upload them from your dashboard.",
    ),
    "under_review": (
        "Documents received",
        "Your documents have been received and our team will review your application.",
    ),
    "clarification_required": (
        "Clarification required",
        "Our team needs more information. Please check the clarification message on your application.",
    ),
    "approved": (
        "Application approved",
        "Your application has been approved by the VyaparSetu review team.",
    ),
    "rejected": (
        "Application rejected",
        "Your application has been rejected. Please review the message from our team.",
    ),
    "document_uploaded": ("Document uploaded", "Your document was uploaded successfully."),
}

ADMIN_MESSAGES = {
    "application_created": "New application created",
    "under_review": "All required documents uploaded",
    "document_uploaded": "Customer uploaded a new document",
    "clarification_required": "Clarification response may require review",
}


def create_notification(
    db: Session,
    *,
    user_id: int | None,
    application_id: int | None,
    channel: str,
    event_type: str,
    recipient: str,
    subject: str,
    message: str,
) -> Notification:
    provider = get_notification_provider()
    notification = Notification(
        user_id=user_id,
        application_id=application_id,
        channel=channel,
        event_type=event_type,
        recipient=recipient,
        subject=subject,
        message=message,
        status="queued",
        provider=provider.provider_name,
    )
    db.add(notification)
    db.flush()

    result = provider.send(
        NotificationSendRequest(
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
        )
    )
    notification.status = result.status
    notification.provider_message_id = result.provider_message_id
    notification.error_message = result.error_message
    if result.status == "sent":
        notification.sent_at = datetime.now(UTC)
    db.add(notification)
    return notification


def notify_customer(db: Session, application: Application, event_type: str) -> Notification:
    subject, message = CUSTOMER_MESSAGES[event_type]
    if event_type == "clarification_required" and application.customer_clarification_message:
        message = application.customer_clarification_message
    return create_notification(
        db,
        user_id=application.owner_id,
        application_id=application.id,
        channel="email",
        event_type=event_type,
        recipient=application.owner.email,
        subject=subject,
        message=message,
    )


def notify_admin(db: Session, application: Application, event_type: str) -> Notification | None:
    if not settings.ADMIN_NOTIFICATION_EMAIL:
        return None
    subject = ADMIN_MESSAGES.get(event_type)
    if subject is None:
        return None
    return create_notification(
        db,
        user_id=None,
        application_id=application.id,
        channel="email",
        event_type=f"admin_{event_type}",
        recipient=settings.ADMIN_NOTIFICATION_EMAIL,
        subject=subject,
        message=f"{subject}: application #{application.id} for {application.business_name}.",
    )


def notify_application_event(db: Session, application: Application, event_type: str) -> None:
    if event_type in CUSTOMER_MESSAGES:
        notify_customer(db, application, event_type)
    notify_admin(db, application, event_type)
