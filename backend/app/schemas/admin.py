from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ApplicationStatus
from app.schemas.application import ApplicationRead
from app.schemas.audit_log import ApplicationAuditLogRead
from app.schemas.certificate import CertificateRead, FeedbackRead
from app.schemas.document import DocumentRead
from app.schemas.document_extraction import DocumentExtractionRead
from app.schemas.tracking import ApplicationTimelineEventRead, GovernmentQueryRead

ADMIN_ALLOWED_STATUSES = {
    ApplicationStatus.DOCUMENTS_PENDING,
    ApplicationStatus.UNDER_REVIEW,
    ApplicationStatus.CLARIFICATION_REQUIRED,
    ApplicationStatus.READY_FOR_FILING,
    ApplicationStatus.FILING_IN_PROGRESS,
    ApplicationStatus.FILED,
    ApplicationStatus.APPROVED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.CERTIFICATE_DELIVERED,
    ApplicationStatus.COMPLETED,
}


class AdminApplicationListResponse(BaseModel):
    items: list[ApplicationRead]
    total: int
    page: int
    page_size: int


class AdminDocumentRead(DocumentRead):
    extractions: list[DocumentExtractionRead] = []


class AdminApplicationDetail(ApplicationRead):
    documents: list[AdminDocumentRead]
    certificates: list[CertificateRead] = []
    feedback: list[FeedbackRead] = []
    timeline_events: list[ApplicationTimelineEventRead] = []
    government_queries: list[GovernmentQueryRead] = []
    audit_logs: list[ApplicationAuditLogRead] = []


class AdminStatusUpdate(BaseModel):
    status: ApplicationStatus
    customer_clarification_message: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> "AdminStatusUpdate":
        if self.status not in ADMIN_ALLOWED_STATUSES:
            raise ValueError("Status is not allowed for admin review")
        if self.status == ApplicationStatus.CLARIFICATION_REQUIRED:
            if not self.customer_clarification_message:
                raise ValueError(
                    "customer_clarification_message is required when status is clarification_required"
                )
        return self


class AdminNotesUpdate(BaseModel):
    internal_admin_notes: str | None = Field(default=None)
    customer_clarification_message: str | None = Field(default=None)


class AdminApplicationFilters(BaseModel):
    service_type: str | None = None
    status: str | None = None
    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None

    model_config = ConfigDict(extra="forbid")
