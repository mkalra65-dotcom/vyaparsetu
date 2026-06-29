from app.core.config import settings
from app.services.ai.base import DocumentAIProvider, DocumentExtractionResult


class OpenAIProvider(DocumentAIProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY must be set to use the OpenAI provider")

    def extract_document_fields(self, file_path: str, document_type: str) -> DocumentExtractionResult:
        raise NotImplementedError(
            "OpenAI extraction is intentionally disabled until paid AI integration is approved."
        )
