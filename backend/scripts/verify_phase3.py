import sys
from pathlib import Path

from fastapi import HTTPException

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.models.application import Application
from app.models.document import Document
from app.models.enums import ApplicationStatus
from app.services.application_workflow import get_required_documents, sync_document_status
from app.services.document_storage import validate_file_size, validate_upload_metadata


class DummyUpload:
    def __init__(self, filename: str, content_type: str) -> None:
        self.filename = filename
        self.content_type = content_type


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def verify_missing_docs_status() -> None:
    application = Application(
        title="GST Registration",
        service_type="gst_registration",
        business_name="Acme",
        owner_id=1,
    )
    sync_document_status(application)
    assert_equal(
        application.status,
        ApplicationStatus.DOCUMENTS_PENDING.value,
        "missing docs status",
    )


def verify_all_docs_uploaded_status() -> None:
    application = Application(
        title="Udyam Registration",
        service_type="udyam_registration",
        business_name="Acme",
        owner_id=1,
    )
    application.documents = [
        Document(
            document_type=document_type,
            original_filename=f"{document_type}.pdf",
            stored_filename=f"{document_type}.pdf",
            file_path=f"/tmp/{document_type}.pdf",
            mime_type="application/pdf",
            file_size=1024,
            uploaded_by_user_id=1,
        )
        for document_type in get_required_documents(application.service_type)
    ]
    sync_document_status(application)
    assert_equal(
        application.status,
        ApplicationStatus.UNDER_REVIEW.value,
        "all docs uploaded status",
    )


def verify_invalid_file_type_rejected() -> None:
    try:
        validate_upload_metadata(DummyUpload("script.exe", "application/octet-stream"))
    except HTTPException as exc:
        assert_equal(exc.status_code, 400, "invalid file status code")
        return
    raise AssertionError("invalid file type was not rejected")


def verify_oversized_file_rejected() -> None:
    try:
        validate_file_size(10 * 1024 * 1024 + 1)
    except HTTPException as exc:
        assert_equal(exc.status_code, 413, "oversized file status code")
        return
    raise AssertionError("oversized file was not rejected")


def main() -> None:
    verify_missing_docs_status()
    verify_all_docs_uploaded_status()
    verify_invalid_file_type_rejected()
    verify_oversized_file_rejected()
    print("Phase 3 verification passed")


if __name__ == "__main__":
    main()
