from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider
from app.services.whatsapp.mock_provider import MockWhatsAppProvider


def get_whatsapp_provider() -> WhatsAppProvider:
    provider = settings.WHATSAPP_PROVIDER.lower()
    if provider == "mock":
        return MockWhatsAppProvider()
    if provider in {"meta", "cloud_api", "twilio", "360dialog"}:
        raise NotImplementedError(f"WhatsApp provider is not integrated yet: {settings.WHATSAPP_PROVIDER}")
    raise ValueError(f"Unsupported WHATSAPP_PROVIDER: {settings.WHATSAPP_PROVIDER}")
