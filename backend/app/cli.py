import typer

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.models.lead import Lead
from app.models.user import User

cli = typer.Typer(help="VyaparSetu backend management commands.")


@cli.command()
def create_first_admin() -> None:
    if not settings.FIRST_ADMIN_EMAIL or not settings.FIRST_ADMIN_PASSWORD:
        raise typer.BadParameter(
            "Set FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD before creating the first admin."
        )

    db = SessionLocal()
    try:
        existing_user = (
            db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL.lower()).first()
        )
        if existing_user is not None:
            typer.echo("Admin user already exists.")
            return

        admin = User(
            email=settings.FIRST_ADMIN_EMAIL.lower(),
            full_name=settings.FIRST_ADMIN_FULL_NAME,
            hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        typer.echo("First admin user created.")
    finally:
        db.close()


@cli.command()
def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@vyaparsetu.local").first()
        if admin is None:
            admin = User(
                email="admin@vyaparsetu.local",
                full_name="Demo Admin",
                hashed_password=get_password_hash("AdminPass123"),
                is_active=True,
                is_admin=True,
            )
            db.add(admin)

        customer = db.query(User).filter(User.email == "customer@vyaparsetu.local").first()
        if customer is None:
            customer = User(
                email="customer@vyaparsetu.local",
                full_name="Demo Customer",
                hashed_password=get_password_hash("CustomerPass123"),
                is_active=True,
                is_admin=False,
            )
            db.add(customer)
            db.flush()

        if db.query(Application).count() == 0:
            db.add_all(
                [
                    Application(
                        title="GST Registration",
                        service_type="gst_registration",
                        status=ApplicationStatus.DOCUMENTS_PENDING.value,
                        business_name="Demo Kirana Store",
                        proprietor_name="Demo Customer",
                        applicant_mobile="9999999999",
                        applicant_email="customer@vyaparsetu.local",
                        pan_number="ABCDE1234F",
                        business_address="Main Market",
                        city="Delhi",
                        state="Delhi",
                        pincode="110001",
                        business_type="Retail",
                        business_constitution="Proprietorship",
                        owner_id=customer.id,
                    ),
                    Application(
                        title="Udyam Registration",
                        service_type="udyam_registration",
                        status=ApplicationStatus.UNDER_REVIEW.value,
                        business_name="Demo Manufacturing",
                        proprietor_name="Demo Customer",
                        applicant_mobile="9999999999",
                        applicant_email="customer@vyaparsetu.local",
                        pan_number="ABCDE1234F",
                        business_address="Industrial Area",
                        city="Noida",
                        state="Uttar Pradesh",
                        pincode="201301",
                        business_type="Manufacturing",
                        enterprise_type="micro",
                        owner_id=customer.id,
                    ),
                ]
            )

        if db.query(Lead).count() == 0:
            db.add(
                Lead(
                    name="Demo Lead",
                    mobile="8888888888",
                    email="lead@example.com",
                    service_interest="gst_registration",
                    message="Need help with GST registration",
                    status="new",
                )
            )

        db.commit()
        typer.echo("Demo data seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
