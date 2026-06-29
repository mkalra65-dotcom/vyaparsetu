from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def validate_upload_metadata(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, JPG, JPEG, and PNG files are allowed",
        )


def validate_file_size(file_size: int) -> None:
    if file_size > settings.MAX_UPLOAD_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size cannot exceed 10MB",
        )


def build_upload_path(application_id: int, original_filename: str) -> tuple[Path, str]:
    upload_dir = Path(settings.UPLOAD_DIR) / str(application_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{suffix}"
    return upload_dir / stored_filename, stored_filename


def remove_uploaded_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists() and path.is_file():
        path.unlink()
