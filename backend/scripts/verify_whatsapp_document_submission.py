import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints.admin import read_admin_application_detail
from app.core.config import settings
from app.db.base import Base
from app.models.document import Document
from app.models.enums import ServiceType
from app.models.user import User
from app.models.whatsapp import ConversationMessage, ConversationSession
from app.services.whatsapp.conversation import handle_media_message, handle_text_message
from app.services.whatsapp.mock_provider import MockWhatsAppProvider


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def media_message(
    *,
    provider_message_id: str,
    provider_media_id: str,
    caption: str,
    filename: str,
    mime_type: str = "application/pdf",
) -> dict:
    return {
        "from": "919999999999",
        "id": provider_message_id,
        "type": "document",
        "document": {
            "id": provider_media_id,
            "caption": caption,
            "filename": filename,
            "mime_type": mime_type,
        },
    }


def upload_document(db, message: dict) -> None:
    handle_media_message(
        db,
        phone_number=message["from"],
        wa_id=message["from"],
        display_name="WhatsApp Customer",
        provider_message_id=message["id"],
        message_type=message["type"],
        media_payload=message["document"],
        raw_payload=message,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as upload_dir:
        settings.UPLOAD_DIR = upload_dir
        db = build_session()
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password="hash",
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.flush()

        session = handle_text_message(
            db,
            phone_number="919999999999",
            wa_id="919999999999",
            display_name="WhatsApp Customer",
            provider_message_id="wamid.service.gst",
            message_body="GST",
            raw_payload={"from": "919999999999", "id": "wamid.service.gst", "type": "text"},
        )
        db.commit()
        db.refresh(session)

        assert_true(session.application_id is not None, "GST application created via WhatsApp")
        assert_true(session.application.service_type == ServiceType.GST_REGISTRATION.value, "application is GST")

        MockWhatsAppProvider.seed_media(
            "media_pan",
            content=b"%PDF-1.4 pan document",
            mime_type="application/pdf",
            filename="pan_card.pdf",
        )
        MockWhatsAppProvider.seed_media(
            "media_aadhaar",
            content=b"%PDF-1.4 aadhaar document",
            mime_type="application/pdf",
            filename="aadhaar_card.pdf",
        )

        upload_document(
            db,
            media_message(
                provider_message_id="wamid.media.pan",
                provider_media_id="media_pan",
                caption="PAN",
                filename="pan_card.pdf",
            ),
        )
        upload_document(
            db,
            media_message(
                provider_message_id="wamid.media.aadhaar",
                provider_media_id="media_aadhaar",
                caption="Aadhaar",
                filename="aadhaar_card.pdf",
            ),
        )
        db.commit()

        session = db.get(ConversationSession, session.id)
        documents = (
            db.query(Document)
            .filter(Document.application_id == session.application_id)
            .order_by(Document.document_type.asc())
            .all()
        )
        document_types = {document.document_type for document in documents}
        assert_true("pan_card" in document_types, "PAN uploaded")
        assert_true("aadhaar_card" in document_types, "Aadhaar uploaded")
        assert_true(all(Path(document.file_path).exists() for document in documents), "documents stored")
        assert_true(all(document.source_channel == "whatsapp" for document in documents), "source channel persisted")
        assert_true(
            {document.provider_media_id for document in documents} == {"media_pan", "media_aadhaar"},
            "provider media ids persisted",
        )
        assert_true(all(document.application_id == session.application_id for document in documents), "application linked")

        media_messages = (
            db.query(ConversationMessage)
            .filter(
                ConversationMessage.application_id == session.application_id,
                ConversationMessage.direction == "inbound",
                ConversationMessage.message_type == "document",
            )
            .all()
        )
        assert_true(len(media_messages) == 2, "inbound media events stored in conversation_messages")
        assert_true(all((message.raw_payload or {}).get("document_id") for message in media_messages), "messages linked to documents")

        admin_detail = read_admin_application_detail(session.application_id, db=db, admin_user=admin)
        admin_document_types = {document["document_type"] for document in admin_detail["documents"]}
        assert_true({"pan_card", "aadhaar_card"}.issubset(admin_document_types), "admin dashboard can see uploaded documents")

        print("WhatsApp document submission verification passed")


if __name__ == "__main__":
    main()
