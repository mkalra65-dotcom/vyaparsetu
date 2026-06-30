from uuid import uuid4

from app.services.whatsapp.base import (
    WhatsAppMediaDownload,
    WhatsAppMediaRequest,
    WhatsAppProvider,
    WhatsAppSendRequest,
    WhatsAppSendResult,
)


class MockWhatsAppProvider(WhatsAppProvider):
    provider_name = "mock_whatsapp"
    _media_store: dict[str, WhatsAppMediaDownload] = {}

    def send_text(self, request: WhatsAppSendRequest) -> WhatsAppSendResult:
        return WhatsAppSendResult(status="sent", provider_message_id=f"mock_wa_{uuid4().hex}")

    @classmethod
    def seed_media(
        cls,
        provider_media_id: str,
        *,
        content: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> None:
        cls._media_store[provider_media_id] = WhatsAppMediaDownload(
            content=content,
            mime_type=mime_type,
            filename=filename,
        )

    def download_media(self, request: WhatsAppMediaRequest) -> WhatsAppMediaDownload:
        media = self._media_store.get(request.provider_media_id)
        if media is None:
            raise FileNotFoundError(f"Mock WhatsApp media not found: {request.provider_media_id}")
        return media
