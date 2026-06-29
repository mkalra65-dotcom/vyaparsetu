from app.core.config import settings
from app.services.notifications.base import NotificationProvider
from app.services.notifications.email_provider import EmailNotificationProvider
from app.services.notifications.mock_provider import MockNotificationProvider
from app.services.notifications.whatsapp_provider import WhatsAppNotificationProvider


def get_notification_provider() -> NotificationProvider:
    provider = settings.NOTIFICATION_PROVIDER.lower()
    if provider == "mock":
        return MockNotificationProvider()
    if provider == "email":
        return EmailNotificationProvider()
    if provider == "whatsapp":
        return WhatsAppNotificationProvider()
    if provider == "sms":
        raise NotImplementedError("SMS provider is not implemented yet")
    raise ValueError(f"Unsupported NOTIFICATION_PROVIDER: {settings.NOTIFICATION_PROVIDER}")
