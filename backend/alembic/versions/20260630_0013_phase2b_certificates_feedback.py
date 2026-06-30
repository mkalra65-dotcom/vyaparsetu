"""Phase 2B certificates and feedback

Revision ID: 20260630_0013
Revises: 20260630_0012
Create Date: 2026-06-30 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0013"
down_revision: str | None = "20260630_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("certificate_type", sa.String(length=100), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_certificates_application_id"), "certificates", ["application_id"], unique=False)
    op.create_index(op.f("ix_certificates_id"), "certificates", ["id"], unique=False)

    op.create_table(
        "customer_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customer_feedback_application_id"), "customer_feedback", ["application_id"], unique=False)
    op.create_index(op.f("ix_customer_feedback_id"), "customer_feedback", ["id"], unique=False)
    op.create_index(op.f("ix_customer_feedback_user_id"), "customer_feedback", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_customer_feedback_user_id"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_id"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_application_id"), table_name="customer_feedback")
    op.drop_table("customer_feedback")
    op.drop_index(op.f("ix_certificates_id"), table_name="certificates")
    op.drop_index(op.f("ix_certificates_application_id"), table_name="certificates")
    op.drop_table("certificates")
