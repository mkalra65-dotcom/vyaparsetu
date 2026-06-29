"""Application workflow fields

Revision ID: 20260629_0002
Revises: 20260629_0001
Create Date: 2026-06-29 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_0002"
down_revision: str | None = "20260629_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("service_type", sa.String(length=50), nullable=True))
    op.add_column("applications", sa.Column("business_name", sa.String(length=255), nullable=True))
    op.add_column("applications", sa.Column("proprietor_name", sa.String(length=255), nullable=True))
    op.add_column("applications", sa.Column("pan_number", sa.String(length=20), nullable=True))
    op.add_column("applications", sa.Column("aadhaar_number", sa.String(length=20), nullable=True))
    op.add_column("applications", sa.Column("business_address", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("state", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("business_constitution", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("annual_turnover", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("food_business_type", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("fssai_license_category", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("enterprise_type", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("investment_amount", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("customer_clarification_message", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("internal_admin_notes", sa.Text(), nullable=True))

    op.execute("UPDATE applications SET service_type = 'gst_registration' WHERE service_type IS NULL")
    op.execute("UPDATE applications SET business_name = title WHERE business_name IS NULL")
    op.alter_column("applications", "service_type", nullable=False)
    op.alter_column("applications", "business_name", nullable=False)


def downgrade() -> None:
    op.drop_column("applications", "internal_admin_notes")
    op.drop_column("applications", "customer_clarification_message")
    op.drop_column("applications", "investment_amount")
    op.drop_column("applications", "enterprise_type")
    op.drop_column("applications", "fssai_license_category")
    op.drop_column("applications", "food_business_type")
    op.drop_column("applications", "annual_turnover")
    op.drop_column("applications", "business_constitution")
    op.drop_column("applications", "state")
    op.drop_column("applications", "business_address")
    op.drop_column("applications", "aadhaar_number")
    op.drop_column("applications", "pan_number")
    op.drop_column("applications", "proprietor_name")
    op.drop_column("applications", "business_name")
    op.drop_column("applications", "service_type")
