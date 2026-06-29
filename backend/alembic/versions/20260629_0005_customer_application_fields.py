"""Customer application fields

Revision ID: 20260629_0005
Revises: 20260629_0004
Create Date: 2026-06-29 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_0005"
down_revision: str | None = "20260629_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("applicant_email", sa.String(length=255), nullable=True))
    op.add_column("applications", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("pincode", sa.String(length=20), nullable=True))
    op.add_column("applications", sa.Column("business_type", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("nature_of_business", sa.String(length=255), nullable=True))
    op.add_column("applications", sa.Column("principal_place_of_business", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("bank_account_details", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("expected_turnover", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("food_category", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("premises_address", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("license_type_suggestion", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("enterprise_name", sa.String(length=255), nullable=True))
    op.add_column("applications", sa.Column("type_of_organisation", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("major_activity", sa.String(length=100), nullable=True))
    op.add_column("applications", sa.Column("nic_code", sa.String(length=50), nullable=True))
    op.add_column("applications", sa.Column("turnover", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "turnover")
    op.drop_column("applications", "nic_code")
    op.drop_column("applications", "major_activity")
    op.drop_column("applications", "type_of_organisation")
    op.drop_column("applications", "enterprise_name")
    op.drop_column("applications", "license_type_suggestion")
    op.drop_column("applications", "premises_address")
    op.drop_column("applications", "food_category")
    op.drop_column("applications", "expected_turnover")
    op.drop_column("applications", "bank_account_details")
    op.drop_column("applications", "principal_place_of_business")
    op.drop_column("applications", "nature_of_business")
    op.drop_column("applications", "business_type")
    op.drop_column("applications", "pincode")
    op.drop_column("applications", "city")
    op.drop_column("applications", "applicant_email")
