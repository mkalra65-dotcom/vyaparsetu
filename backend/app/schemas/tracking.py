from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.application import ApplicationRead
from app.schemas.certificate import CertificateRead, FeedbackRead
from app.schemas.document import DocumentRead


class ApplicationTimelineEventRead(BaseModel):
    id: int
    application_id: int
    event_type: str
    title: str
    description: str | None = None
    actor_user_id: int | None = None
    source_channel: str
    metadata_json: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GovernmentQueryRead(BaseModel):
    id: int
    application_id: int
    raised_by_user_id: int
    response_document_id: int | None = None
    message: str
    required_document_type: str
    due_date: date
    status: str
    sent_to_customer_at: datetime | None = None
    responded_at: datetime | None = None
    overdue_alerted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        return self.status == "open" and self.due_date < date.today()

    model_config = ConfigDict(from_attributes=True)


class GovernmentQueryCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    required_document_type: str = Field(min_length=1, max_length=100)
    due_date: date


class TimelineEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ApplicationTrackingRead(BaseModel):
    application: ApplicationRead
    timeline_events: list[ApplicationTimelineEventRead]
    government_queries: list[GovernmentQueryRead]
    documents: list[DocumentRead]
    certificates: list[CertificateRead]
    feedback: list[FeedbackRead]
