import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.v1.endpoints.admin import (
    list_admin_leads,
    read_admin_analytics,
    read_admin_lead,
    update_admin_lead_status,
)
from app.api.v1.endpoints.leads import create_lead
from app.api.v1.endpoints.pricing import read_pricing
from app.db.base import Base
from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadStatus, LeadUpdate


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def main() -> None:
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
        Application(
            title="GST Registration",
            service_type="gst_registration",
            status=ApplicationStatus.APPROVED.value,
            business_name="Acme",
            pan_number="ABCDE1234F",
            business_address="Market Road",
            state="Delhi",
            business_constitution="Proprietorship",
            owner_id=customer.id,
        )
    )
    db.commit()

    lead = create_lead(
        LeadCreate(
            name="Launch Lead",
            mobile="9999999999",
            email="lead@example.com",
            service_interest="gst_registration",
            message="Please call me",
        ),
        db,
    )
    assert_true(lead.id is not None, "lead created")
    assert_true(len(list_admin_leads(db=db, _=admin)) == 1, "admin can list leads")
    assert_true(read_admin_lead(lead.id, db=db, _=admin).name == "Launch Lead", "admin can read lead")
    updated = update_admin_lead_status(
        lead.id,
        LeadUpdate(status=LeadStatus.CONTACTED),
        db=db,
        _=admin,
    )
    assert_true(updated.status == "contacted", "lead status updated")
    analytics = read_admin_analytics(db=db, _=admin)
    assert_true(analytics["leads"] == 1, "analytics leads")
    assert_true(analytics["applications"] == 1, "analytics applications")
    assert_true("gst_registration" in read_pricing(), "pricing configured")
    print("Phase 9 verification passed")


if __name__ == "__main__":
    main()
