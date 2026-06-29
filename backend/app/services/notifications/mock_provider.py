from uuid import uuid4

from app.services.notifications.base import (
    NotificationProvider,
    NotificationSendRequest,
    NotificationSendResult,
)


class MockNotificationProvider(NotificationProvider):
    provider_name = "mock"

    def send(self, request: NotificationSendRequest) -> NotificationSendResult:
        return NotificationSendResult(status="sent", provider_message_id=f"mock_{uuid4().hex}")
