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
    APPROVED = "approved"
    REJECTED = "rejected"
