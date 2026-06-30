import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints.admin import (
    create_admin_government_query,
    create_admin_timeline_event,
    list_overdue_government_queries,
    update_admin_application_status,
)
from app.api.v1.endpoints.applications import create_application, read_application_tracking
from app.core.config import settings
from app.db.base import Base
from app.models.audit_log import ApplicationAuditLog
from app.models.application import Application
from app.models.government_query import GovernmentQuery
from app.models.notification import Notification
from app.models.user import User
from app.models.whatsapp import ConversationMessage, ConversationSession, WhatsAppContact
from app.schemas.admin import AdminStatusUpdate
from app.schemas.application import ApplicationCreate
from app.schemas.tracking import GovernmentQueryCreate, TimelineEventCreate
from app.services.whatsapp.conversation import handle_media_message
from app.services.whatsapp.mock_provider import MockWhatsAppProvider


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


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
        customer = User(
            email="customer@example.com",
            full_name="Customer User",
            hashed_password="hash",
            is_active=True,
            is_admin=False,
        )
        db.add_all([admin, customer])
        db.flush()

        contact = WhatsAppContact(
            phone_number="919999999999",
            wa_id="919999999999",
            display_name="Customer User",
            user_id=customer.id,
            consent_status="inbound_opt_in",
        )
        db.add(contact)
        db.flush()

        application_data = ApplicationCreate(
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
        )
        application_response = create_application(application_data, db=db, current_user=customer)
        application_id = application_response["id"]
        session = ConversationSession(
            contact_id=contact.id,
            application_id=application_id,
            state="draft_application_created",
            selected_service_type="gst_registration",
        )
        db.add(session)
        db.commit()

        application = db.get(Application, application_id)
        assert_true(application is not None, "application created")

        update_admin_application_status(
            application_id,
            AdminStatusUpdate(status="under_review", note="Review started"),
            db=db,
            admin_user=admin,
        )

        create_admin_government_query(
            application_id,
            GovernmentQueryCreate(
                message="Please upload updated Aadhaar proof.",
                required_document_type="aadhaar_card",
                due_date=date.today() + timedelta(days=3),
            ),
            db=db,
            admin_user=admin,
        )
        open_query = db.query(GovernmentQuery).filter_by(application_id=application_id, status="open").first()
        assert_true(open_query is not None, "government query created")

        MockWhatsAppProvider.seed_media(
            "media_aadhaar_phase2a",
            content=b"%PDF-1.4 aadhaar response",
            mime_type="application/pdf",
            filename="aadhaar_card.pdf",
        )
        handle_media_message(
            db,
            phone_number="919999999999",
            wa_id="919999999999",
            display_name="Customer User",
            provider_message_id="wamid.phase2a.aadhaar",
            message_type="document",
            media_payload={
                "id": "media_aadhaar_phase2a",
                "caption": "Aadhaar",
                "filename": "aadhaar_card.pdf",
                "mime_type": "application/pdf",
            },
            raw_payload={"id": "wamid.phase2a.aadhaar", "type": "document"},
        )
        db.commit()
        db.refresh(open_query)
        assert_true(open_query.status == "responded", "customer response received via WhatsApp")
        assert_true(open_query.response_document_id is not None, "query linked to response document")

        create_admin_timeline_event(
            application_id,
            TimelineEventCreate(
                event_type="filing_submitted",
                title="Filing submitted",
                description="Submitted to GST portal.",
            ),
            db=db,
            admin_user=admin,
        )
        update_admin_application_status(
            application_id,
            AdminStatusUpdate(status="approved", note="Approved by department"),
            db=db,
            admin_user=admin,
        )
        create_admin_timeline_event(
            application_id,
            TimelineEventCreate(
                event_type="certificate_delivered",
                title="Certificate delivered",
                description="Certificate sent to customer.",
            ),
            db=db,
            admin_user=admin,
        )

        create_admin_government_query(
            application_id,
            GovernmentQueryCreate(
                message="Overdue proof request.",
                required_document_type="bank_account_proof",
                due_date=date.today() - timedelta(days=1),
            ),
            db=db,
            admin_user=admin,
        )
        overdue = list_overdue_government_queries(db=db, admin_user=admin)
        assert_true(len(overdue) >= 1, "overdue query detected")
        assert_true(db.query(Notification).filter_by(event_type="query_overdue").count() >= 1, "overdue alert created")

        tracking = read_application_tracking(application_id, db=db, current_user=customer)
        event_types = {event.event_type for event in tracking["timeline_events"]}
        expected_events = {
            "application_created",
            "review_started",
            "government_query_received",
            "document_uploaded",
            "customer_response_received",
            "filing_submitted",
            "application_approved",
            "certificate_delivered",
        }
        assert_true(expected_events.issubset(event_types), "significant timeline events created")
        assert_true(len(tracking["government_queries"]) >= 2, "tracking endpoint returns queries")
        assert_true(len(tracking["documents"]) >= 1, "tracking endpoint returns documents")

        outbound_updates = (
            db.query(ConversationMessage)
            .filter(
                ConversationMessage.application_id == application_id,
                ConversationMessage.direction == "outbound",
            )
            .all()
        )
        assert_true(any((message.raw_payload or {}).get("event_type") for message in outbound_updates), "WhatsApp status updates created")
        assert_true(db.query(ApplicationAuditLog).filter_by(application_id=application_id).count() >= 8, "actions audited")

        print("Phase 2A tracking and query verification passed")


if __name__ == "__main__":
    main()
