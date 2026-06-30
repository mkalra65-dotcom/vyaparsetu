from dataclasses import dataclass


@dataclass(frozen=True)
class WhatsAppSendRequest:
    recipient: str
    message: str


@dataclass(frozen=True)
class WhatsAppSendResult:
    status: str
    provider_message_id: str | None = None
    error_message: str | None = None


class WhatsAppProvider:
    provider_name: str

    def send_text(self, request: WhatsAppSendRequest) -> WhatsAppSendResult:
        raise NotImplementedError
