import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints.admin import list_admin_notifications
from app.api.v1.endpoints.notifications import list_my_notifications
from app.core.config import settings
from app.db.base import Base
from app.models.application import Application
from app.models.document import Document
from app.models.enums import ApplicationStatus
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import notify_application_event


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def seed_data(db):
    customer = User(
        email="customer@example.com",
        full_name="Customer User",
        hashed_password="hash",
        is_active=True,
        is_admin=False,
    )
    other_customer = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password="hash",
        is_active=True,
        is_admin=False,
    )
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hash",
        is_active=True,
        is_admin=True,
    )
    db.add_all([customer, other_customer, admin])
    db.flush()

    application = Application(
        title="GST Application",
        service_type="gst_registration",
        status=ApplicationStatus.DOCUMENTS_PENDING.value,
        business_name="Acme Traders",
        proprietor_name="Customer User",
        applicant_mobile="9999999999",
        pan_number="ABCDE1234F",
        business_address="Main Street",
        state="Delhi",
        business_constitution="Proprietorship",
        owner_id=customer.id,
    )
    db.add(application)
    db.flush()
    document = Document(
        application_id=application.id,
        document_type="pan_card",
        original_filename="pan.pdf",
        stored_filename="pan.pdf",
        file_path="/tmp/pan.pdf",
        mime_type="application/pdf",
        file_size=1024,
        uploaded_by_user_id=customer.id,
    )
    db.add(document)
    db.commit()
    db.refresh(application)
    return customer, other_customer, admin, application, document


def main() -> None:
    settings.ADMIN_NOTIFICATION_EMAIL = "ops@example.com"
    db = build_session()
    customer, other_customer, admin, application, _ = seed_data(db)

    notify_application_event(db, application, "application_created")
    notify_application_event(db, application, "approved")
    notify_application_event(db, application, "document_uploaded")
    db.commit()

    notifications = db.query(Notification).order_by(Notification.created_at.asc()).all()
    assert_true(any(n.event_type == "application_created" for n in notifications), "application notification")
    assert_true(any(n.event_type == "approved" for n in notifications), "status notification")
    assert_true(any(n.event_type == "document_uploaded" for n in notifications), "document notification")
    assert_true(all(n.status == "sent" for n in notifications), "mock provider marks sent")
    assert_true(all(n.provider == "mock" for n in notifications), "mock provider persisted")

    customer_notifications = list_my_notifications(db=db, current_user=customer)
    other_notifications = list_my_notifications(db=db, current_user=other_customer)
    admin_notifications = list_admin_notifications(db=db, _=admin)
    assert_true(len(customer_notifications) == 3, "customer sees own notifications")
    assert_true(len(other_notifications) == 0, "customer cannot see others")
    assert_true(len(admin_notifications) >= len(customer_notifications), "admin can see all notifications")

    print("Phase 8 verification passed")


if __name__ == "__main__":
    main()
