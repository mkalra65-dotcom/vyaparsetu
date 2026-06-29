from app.core.config import settings
from app.services.ai.base import DocumentAIProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.openai_provider import OpenAIProvider


def get_ai_provider() -> DocumentAIProvider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "mock":
        return MockAIProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider in {"gemini", "claude"}:
        raise NotImplementedError(f"{provider} provider is not implemented yet")
    raise ValueError(f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}")
