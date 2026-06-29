"""Admin review audit logs

Revision ID: 20260629_0004
Revises: 20260629_0003
Create Date: 2026-06-29 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_0004"
down_revision: str | None = "20260629_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("applicant_mobile", sa.String(length=20), nullable=True))

    op.create_table(
        "application_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_audit_logs_actor_user_id"),
        "application_audit_logs",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_audit_logs_application_id"),
        "application_audit_logs",
        ["application_id"],
        unique=False,
    )
    op.create_index(op.f("ix_application_audit_logs_id"), "application_audit_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_application_audit_logs_id"), table_name="application_audit_logs")
    op.drop_index(
        op.f("ix_application_audit_logs_application_id"),
        table_name="application_audit_logs",
    )
    op.drop_index(
        op.f("ix_application_audit_logs_actor_user_id"),
        table_name="application_audit_logs",
    )
    op.drop_table("application_audit_logs")
    op.drop_column("applications", "applicant_mobile")
