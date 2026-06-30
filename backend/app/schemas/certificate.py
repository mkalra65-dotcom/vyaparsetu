from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CertificateRead(BaseModel):
    id: int
    application_id: int
    certificate_type: str
    original_filename: str
    stored_filename: str
    file_path: str
    mime_type: str
    file_size: int
    uploaded_by: int
    uploaded_at: datetime
    delivered_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback: str | None = Field(default=None, max_length=2000)


class FeedbackRead(BaseModel):
    id: int
    application_id: int
    user_id: int
    rating: int
    feedback: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
