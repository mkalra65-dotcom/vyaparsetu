from enum import StrEnum


class ServiceType(StrEnum):
    GST_REGISTRATION = "gst_registration"
    FSSAI_REGISTRATION = "fssai_registration"
    UDYAM_REGISTRATION = "udyam_registration"


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    DOCUMENTS_PENDING = "documents_pending"
    UNDER_REVIEW = "under_review"
    CLARIFICATION_REQUIRED = "clarification_required"
    READY_FOR_FILING = "ready_for_filing"
    FILING_IN_PROGRESS = "filing_in_progress"
    FILED = "filed"
    APPROVED = "approved"
    REJECTED = "rejected"
    CERTIFICATE_DELIVERED = "certificate_delivered"
    COMPLETED = "completed"
