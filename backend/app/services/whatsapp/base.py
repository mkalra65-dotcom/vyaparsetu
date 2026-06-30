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


@dataclass(frozen=True)
class WhatsAppMediaRequest:
    provider_media_id: str


@dataclass(frozen=True)
class WhatsAppMediaDownload:
    content: bytes
    mime_type: str
    filename: str | None = None


class WhatsAppProvider:
    provider_name: str

    def send_text(self, request: WhatsAppSendRequest) -> WhatsAppSendResult:
        raise NotImplementedError

    def download_media(self, request: WhatsAppMediaRequest) -> WhatsAppMediaDownload:
        raise NotImplementedError
