import asyncio
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import Headers, UploadFile

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints.admin import (
    deliver_certificate,
    update_admin_application_status,
    upload_application_certificate,
)
from app.api.v1.endpoints.applications import (
    create_application,
    download_certificate,
    read_application_tracking,
    submit_application_feedback,
)
from app.core.config import settings
from app.db.base import Base
from app.models.audit_log import ApplicationAuditLog
from app.models.application_timeline import ApplicationTimelineEvent
from app.models.certificate import Certificate
from app.models.enums import ApplicationStatus
from app.models.feedback import CustomerFeedback
from app.models.user import User
from app.models.whatsapp import ConversationMessage, WhatsAppContact
from app.schemas.admin import AdminStatusUpdate
from app.schemas.application import ApplicationCreate
from app.schemas.certificate import FeedbackCreate


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def build_upload_file(filename: str, content: bytes, content_type: str = "application/pdf") -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


async def main() -> None:
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
        customer = User(
            email="customer@example.com",
            full_name="Customer User",
            hashed_password="hash",
            is_active=True,
            is_admin=False,
        )
        db.add_all([admin, customer])
        db.flush()
        db.add(
            WhatsAppContact(
                phone_number="919999999999",
                wa_id="919999999999",
                display_name="Customer User",
                user_id=customer.id,
                consent_status="inbound_opt_in",
            )
        )
        db.flush()

        application_response = create_application(
            ApplicationCreate(
                title="GST Registration",
                service_type="gst_registration",
                business_name="Acme Traders",
                proprietor_name="Customer User",
                applicant_mobile="919999999999",
                applicant_email=customer.email,
                pan_number="ABCDE1234F",
                business_address="Main Street",
                state="Delhi",
                business_constitution="Proprietorship",
            ),
            db=db,
            current_user=customer,
        )
        application_id = application_response["id"]

        filed_detail = update_admin_application_status(
            application_id,
            AdminStatusUpdate(status=ApplicationStatus.FILED, note="Filed with GST department"),
            db=db,
            admin_user=admin,
        )
        assert_true(filed_detail["status"] == ApplicationStatus.FILED.value, "application reaches filed")

        approved_detail = update_admin_application_status(
            application_id,
            AdminStatusUpdate(status=ApplicationStatus.APPROVED, note="Approved by GST department"),
            db=db,
            admin_user=admin,
        )
        assert_true(approved_detail["status"] == ApplicationStatus.APPROVED.value, "application reaches approved")

        uploaded_detail = await upload_application_certificate(
            application_id,
            db=db,
            admin_user=admin,
            certificate_type="gst_certificate",
            file=build_upload_file("gst_certificate.pdf", b"%PDF-1.4 certificate"),
        )
        assert_true(len(uploaded_detail["certificates"]) == 1, "certificate uploaded")
        certificate_id = uploaded_detail["certificates"][0].id
        certificate = db.get(Certificate, certificate_id)
        assert_true(certificate is not None and Path(certificate.file_path).exists(), "certificate stored")

        tracking = read_application_tracking(application_id, db=db, current_user=customer)
        assert_true(len(tracking["certificates"]) == 1, "certificate visible on tracking page")
        download_response = download_certificate(certificate_id, db=db, current_user=customer)
        assert_true(download_response.filename == "gst_certificate.pdf", "certificate download available")

        delivered_detail = deliver_certificate(certificate_id, db=db, admin_user=admin)
        assert_true(delivered_detail["status"] == ApplicationStatus.CERTIFICATE_DELIVERED.value, "certificate delivered")
        db.refresh(certificate)
        assert_true(certificate.delivered_at is not None, "certificate delivered_at set")

        completed_detail = update_admin_application_status(
            application_id,
            AdminStatusUpdate(status=ApplicationStatus.COMPLETED, note="Lifecycle complete"),
            db=db,
            admin_user=admin,
        )
        assert_true(completed_detail["status"] == ApplicationStatus.COMPLETED.value, "application completed")

        feedback = submit_application_feedback(
            application_id,
            FeedbackCreate(rating=5, feedback="Smooth process."),
            db=db,
            current_user=customer,
        )
        assert_true(feedback.rating == 5, "feedback captured")
        assert_true(db.query(CustomerFeedback).filter_by(application_id=application_id).count() == 1, "feedback stored")

        event_types = {
            row.event_type
            for row in db.query(ApplicationTimelineEvent).filter_by(application_id=application_id).all()
        }
        expected_events = {
            "application_created",
            "filing_submitted",
            "application_approved",
            "certificate_uploaded",
            "certificate_delivered",
            "feedback_requested",
            "application_completed",
            "feedback_received",
        }
        assert_true(expected_events.issubset(event_types), "timeline events created")
        audit_actions = {
            row.action
            for row in db.query(ApplicationAuditLog).filter_by(application_id=application_id).all()
        }
        assert_true(
            {"application_created", "admin_status_changed", "certificate_uploaded", "certificate_delivered", "feedback_submitted"}.issubset(audit_actions),
            "audit logs created",
        )
        whatsapp_events = {
            (message.raw_payload or {}).get("event_type")
            for message in db.query(ConversationMessage)
            .filter(ConversationMessage.application_id == application_id, ConversationMessage.direction == "outbound")
            .all()
        }
        assert_true("certificate_delivered" in whatsapp_events, "certificate delivery WhatsApp sent")
        assert_true("feedback_requested" in whatsapp_events, "feedback WhatsApp sent")

        print("Phase 2B operational workflow verification passed")


if __name__ == "__main__":
    asyncio.run(main())
