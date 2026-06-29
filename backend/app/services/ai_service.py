from app.models.document import Document
from app.services.ai.provider_factory import get_ai_provider
from app.services.document_intelligence import calculate_application_health


def extract_document_fields(file_path: str) -> dict:
    result = get_ai_provider().extract_document_fields(file_path, "unknown")
    return result.model_dump()


def validate_document(document: Document) -> dict:
    result = get_ai_provider().extract_document_fields(document.file_path, document.document_type)
    return {
        "document_id": document.id,
        "is_valid": not result.validation_warnings,
        "issues": result.validation_warnings,
        "provider": get_ai_provider().provider_name,
    }


def suggest_missing_documents(application) -> list[str]:
    from app.services.application_workflow import get_missing_required_documents

    return get_missing_required_documents(application)


def generate_customer_message(application) -> str:
    _, summary = calculate_application_health(application)
    return summary
