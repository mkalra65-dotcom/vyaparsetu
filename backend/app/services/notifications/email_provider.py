from app.services.notifications.base import (
    NotificationProvider,
    NotificationSendRequest,
    NotificationSendResult,
)


class EmailNotificationProvider(NotificationProvider):
    provider_name = "email"

    def send(self, request: NotificationSendRequest) -> NotificationSendResult:
        return NotificationSendResult(
            status="failed",
            error_message="Real email provider is not integrated yet",
        )
