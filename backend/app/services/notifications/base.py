from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationSendRequest:
    channel: str
    recipient: str
    subject: str
    message: str


@dataclass(frozen=True)
class NotificationSendResult:
    status: str
    provider_message_id: str | None = None
    error_message: str | None = None


class NotificationProvider:
    provider_name: str

    def send(self, request: NotificationSendRequest) -> NotificationSendResult:
        raise NotImplementedError
