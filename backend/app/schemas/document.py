from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    id: int
    application_id: int
    document_type: str = Field(max_length=100)
    original_filename: str
    stored_filename: str
    file_path: str
    mime_type: str
    file_size: int
    uploaded_by_user_id: int
    ai_processing_status: str
    requires_attention: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
