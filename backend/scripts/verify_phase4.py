import sys
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.deps import require_admin
from app.api.v1.endpoints.admin import list_admin_applications, update_admin_application_status
from app.api.v1.endpoints.applications import serialize_application
from app.db.base import Base
from app.models.application import Application
from app.models.audit_log import ApplicationAuditLog
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.admin import AdminStatusUpdate


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
        business_name="Acme Foods",
        proprietor_name="Customer User",
        applicant_mobile="9999999999",
        pan_number="ABCDE1234F",
        business_address="Main Street",
        state="Delhi",
        business_constitution="Proprietorship",
        owner_id=customer.id,
        internal_admin_notes="Internal risk note",
        customer_clarification_message="Please upload bank proof",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return customer, admin, application


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def verify_customer_cannot_access_admin_endpoints(customer: User) -> None:
    try:
        require_admin(customer)
    except HTTPException as exc:
        assert_true(exc.status_code == 403, "customer admin access status code")
        return
    raise AssertionError("customer was allowed through admin guard")


def verify_admin_can_list_all_applications(db, admin: User) -> None:
    response = list_admin_applications(
        db=db,
        admin_user=admin,
        service_type=None,
        status_filter=None,
        search=None,
        created_from=None,
        created_to=None,
        page=1,
        page_size=20,
    )
    assert_true(response["total"] == 1, "admin list total")
    assert_true(response["items"][0]["business_name"] == "Acme Foods", "admin list item")


def verify_customer_visibility(application: Application, customer: User) -> None:
    response = serialize_application(application, customer)
    assert_true(response["internal_admin_notes"] is None, "internal notes hidden")
    assert_true(
        response["customer_clarification_message"] == "Please upload bank proof",
        "clarification visible",
    )


def verify_audit_log_created_on_status_change(db, admin: User, application: Application) -> None:
    payload = AdminStatusUpdate(status=ApplicationStatus.APPROVED, note="Looks complete")
    update_admin_application_status(
        application_id=application.id,
        status_in=payload,
        db=db,
        admin_user=admin,
    )
    audit_log = db.query(ApplicationAuditLog).filter_by(action="admin_status_changed").first()
    assert_true(audit_log is not None, "status audit log exists")
    assert_true(audit_log.old_status == ApplicationStatus.UNDER_REVIEW.value, "audit old status")
    assert_true(audit_log.new_status == ApplicationStatus.APPROVED.value, "audit new status")


def main() -> None:
    db = build_session()
    customer, admin, application = seed_data(db)
    verify_customer_cannot_access_admin_endpoints(customer)
    verify_admin_can_list_all_applications(db, admin)
    verify_customer_visibility(application, customer)
    verify_audit_log_created_on_status_change(db, admin, application)
    print("Phase 4 verification passed")


if __name__ == "__main__":
    main()
