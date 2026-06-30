from uuid import uuid4

from app.services.whatsapp.base import WhatsAppProvider, WhatsAppSendRequest, WhatsAppSendResult


class MockWhatsAppProvider(WhatsAppProvider):
    provider_name = "mock_whatsapp"

    def send_text(self, request: WhatsAppSendRequest) -> WhatsAppSendResult:
        return WhatsAppSendResult(status="sent", provider_message_id=f"mock_wa_{uuid4().hex}")
