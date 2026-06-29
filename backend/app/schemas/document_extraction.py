from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DocumentExtractionRead(BaseModel):
    id: int
    document_id: int
    provider: str
    document_type: str
    extracted_json: dict[str, Any]
    confidence_score: float
    validation_warnings: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
