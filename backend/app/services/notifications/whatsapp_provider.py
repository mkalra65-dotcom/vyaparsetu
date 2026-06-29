from app.services.notifications.base import (
    NotificationProvider,
    NotificationSendRequest,
    NotificationSendResult,
)


class WhatsAppNotificationProvider(NotificationProvider):
    provider_name = "whatsapp"

    def send(self, request: NotificationSendRequest) -> NotificationSendResult:
        return NotificationSendResult(
            status="failed",
            error_message="Real WhatsApp provider is not integrated yet",
        )
