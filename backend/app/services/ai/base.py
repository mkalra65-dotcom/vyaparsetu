from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


SUPPORTED_DOCUMENT_TYPES = {
    "pan_card",
    "aadhaar_card",
    "business_address_proof",
    "food_business_address_proof",
    "bank_account_proof",
}


class DocumentExtractionResult(BaseModel):
    document_type: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=1)
    validation_warnings: list[str] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentAIProvider(ABC):
    provider_name: str

    @abstractmethod
    def extract_document_fields(self, file_path: str, document_type: str) -> DocumentExtractionResult:
        raise NotImplementedError
