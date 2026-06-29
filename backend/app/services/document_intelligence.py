from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.services.ai.provider_factory import get_ai_provider
from app.services.application_workflow import get_missing_required_documents


def calculate_application_health(application: Application) -> tuple[int, str]:
    missing_documents = get_missing_required_documents(application)
    warnings = [
        warning
        for document in application.documents
        for extraction in document.extractions
        for warning in extraction.validation_warnings
    ]

    if missing_documents:
        score = max(40, 80 - (len(missing_documents) * 15))
        summary = f"Missing required documents: {', '.join(missing_documents)}."
    elif warnings:
        score = max(70, 95 - (len(warnings) * 10))
        summary = "Document review needs attention: " + "; ".join(warnings)
    else:
        score = 95
        summary = "All required documents present and validated."
    return score, summary


def refresh_application_review_summary(db: Session, application: Application) -> None:
    score, summary = calculate_application_health(application)
    application.health_score = score
    application.ai_review_summary = summary
    db.add(application)


def process_document_extraction(document_id: int) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return
        provider = get_ai_provider()
        result = provider.extract_document_fields(document.file_path, document.document_type)
        extraction = DocumentExtraction(
            document_id=document.id,
            provider=provider.provider_name,
            document_type=result.document_type,
            extracted_json={
                "document_type": result.document_type,
                "extracted_fields": result.extracted_fields,
                "confidence_score": result.confidence_score,
                "validation_warnings": result.validation_warnings,
                "extracted_at": result.extracted_at.isoformat(),
            },
            confidence_score=result.confidence_score,
            validation_warnings=result.validation_warnings,
        )
        db.add(extraction)
        db.flush()
        db.refresh(document)
        refresh_application_review_summary(db, document.application)
        db.commit()
    finally:
        db.close()


def process_document_extraction_inline(db: Session, document: Document) -> DocumentExtraction:
    provider = get_ai_provider()
    result = provider.extract_document_fields(document.file_path, document.document_type)
    extraction = DocumentExtraction(
        document_id=document.id,
        provider=provider.provider_name,
        document_type=result.document_type,
        extracted_json={
            "document_type": result.document_type,
            "extracted_fields": result.extracted_fields,
            "confidence_score": result.confidence_score,
            "validation_warnings": result.validation_warnings,
            "extracted_at": result.extracted_at.isoformat(),
        },
        confidence_score=result.confidence_score,
        validation_warnings=result.validation_warnings,
    )
    db.add(extraction)
    db.flush()
    db.refresh(document)
    refresh_application_review_summary(db, document.application)
    return extraction
