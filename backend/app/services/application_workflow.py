from app.models.application import Application
from app.models.enums import ApplicationStatus, ServiceType

REQUIRED_DOCUMENTS: dict[ServiceType, set[str]] = {
    ServiceType.GST_REGISTRATION: {
        "pan_card",
        "aadhaar_card",
        "business_address_proof",
        "bank_account_proof",
    },
    ServiceType.FSSAI_REGISTRATION: {
        "photo_id",
        "food_business_address_proof",
        "food_safety_management_plan",
    },
    ServiceType.UDYAM_REGISTRATION: {
        "aadhaar_card",
        "pan_card",
        "business_address_proof",
    },
}


def get_required_documents(service_type: str | ServiceType) -> set[str]:
    return REQUIRED_DOCUMENTS[ServiceType(service_type)]


def get_missing_required_documents(application: Application) -> list[str]:
    uploaded_document_types = {
        document.document_type
        for document in application.documents
        if document.document_type is not None
    }
    missing_documents = get_required_documents(application.service_type) - uploaded_document_types
    return sorted(missing_documents)


def sync_document_status(application: Application) -> None:
    if get_missing_required_documents(application):
        application.status = ApplicationStatus.DOCUMENTS_PENDING.value
    else:
        application.status = ApplicationStatus.UNDER_REVIEW.value
