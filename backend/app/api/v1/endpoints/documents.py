from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.application import Application
from app.models.document import Document
from app.schemas.document import DocumentRead
from app.services.application_workflow import sync_document_status
from app.services.audit import add_application_audit_log
from app.services.document_storage import remove_uploaded_file
from app.services.notification_service import notify_application_event

router = APIRouter()


def get_accessible_document(
    document_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not current_user.is_admin and document.application.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return document


@router.get("/admin/metadata", response_model=list[DocumentRead])
def list_all_document_metadata(db: DbSession, _: AdminUser) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentRead)
def read_document_metadata(
    document_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Document:
    return get_accessible_document(document_id, db, current_user)


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> FileResponse:
    document = get_accessible_document(document_id, db, current_user)
    return FileResponse(
        document.file_path,
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    document = get_accessible_document(document_id, db, current_user)
    application = document.application
    old_status = application.status
    document_type = document.document_type
    original_filename = document.original_filename
    remove_uploaded_file(document.file_path)
    db.delete(document)
    db.flush()
    db.expire(application, ["documents"])
    sync_document_status(application)
    add_application_audit_log(
        db,
        application_id=application.id,
        actor_user_id=current_user.id,
        action="document_deleted",
        old_status=old_status,
        new_status=application.status,
        note=f"Deleted {document_type}: {original_filename}",
    )
    if old_status != application.status:
        notify_application_event(db, application, application.status)
    db.add(application)
    db.commit()
    return None
