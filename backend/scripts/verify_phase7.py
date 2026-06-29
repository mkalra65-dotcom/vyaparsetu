import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints.admin import serialize_admin_application_detail
from app.api.v1.endpoints.applications import serialize_application
from app.db.base import Base
from app.models.application import Application
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.services.document_intelligence import process_document_extraction_inline


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
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="hash",
        is_active=True,
        is_admin=True,
    )
    db.add_all([customer, admin])
    db.flush()

    application = Application(
        title="GST Application",
        service_type="gst_registration",
        status=ApplicationStatus.UNDER_REVIEW.value,
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
    db.refresh(document)
    return customer, admin, application, document


def main() -> None:
    db = build_session()
    customer, admin, application, document = seed_data(db)

    process_document_extraction_inline(db, document)
    db.commit()
    db.refresh(application)
    db.refresh(document)

    extraction = db.query(DocumentExtraction).filter_by(document_id=document.id).first()
    assert_true(extraction is not None, "extraction saved")
    assert_true(extraction.provider == "mock", "mock provider used")
    assert_true(application.health_score is not None, "health score generated")
    assert_true(application.ai_review_summary is not None, "AI review summary generated")

    admin_view = serialize_admin_application_detail(application, admin)
    assert_true(bool(admin_view["documents"][0]["extractions"]), "admin can view extraction")

    customer_view = serialize_application(application, customer)
    assert_true(customer_view["health_score"] is None, "customer health score hidden")
    assert_true(customer_view["ai_review_summary"] is None, "customer summary hidden")

    assert_true(document.ai_processing_status == "processed", "customer sees processed status")
    assert_true(document.requires_attention is False, "customer attention flag available")
    print("Phase 7 verification passed")


if __name__ == "__main__":
    main()
