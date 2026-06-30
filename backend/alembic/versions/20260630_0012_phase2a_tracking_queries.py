"""Phase 2A tracking and government queries

Revision ID: 20260630_0012
Revises: 20260630_0011
Create Date: 2026-06-30 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0012"
down_revision: str | None = "20260630_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_timeline_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("source_channel", sa.String(length=50), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_timeline_events_actor_user_id"), "application_timeline_events", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_application_timeline_events_application_id"), "application_timeline_events", ["application_id"], unique=False)
    op.create_index(op.f("ix_application_timeline_events_event_type"), "application_timeline_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_application_timeline_events_id"), "application_timeline_events", ["id"], unique=False)

    op.create_table(
        "government_queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("raised_by_user_id", sa.Integer(), nullable=False),
        sa.Column("response_document_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("required_document_type", sa.String(length=100), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("sent_to_customer_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overdue_alerted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raised_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["response_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_government_queries_application_id"), "government_queries", ["application_id"], unique=False)
    op.create_index(op.f("ix_government_queries_due_date"), "government_queries", ["due_date"], unique=False)
    op.create_index(op.f("ix_government_queries_id"), "government_queries", ["id"], unique=False)
    op.create_index(op.f("ix_government_queries_raised_by_user_id"), "government_queries", ["raised_by_user_id"], unique=False)
    op.create_index(op.f("ix_government_queries_response_document_id"), "government_queries", ["response_document_id"], unique=False)
    op.create_index(op.f("ix_government_queries_status"), "government_queries", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_government_queries_status"), table_name="government_queries")
    op.drop_index(op.f("ix_government_queries_response_document_id"), table_name="government_queries")
    op.drop_index(op.f("ix_government_queries_raised_by_user_id"), table_name="government_queries")
    op.drop_index(op.f("ix_government_queries_id"), table_name="government_queries")
    op.drop_index(op.f("ix_government_queries_due_date"), table_name="government_queries")
    op.drop_index(op.f("ix_government_queries_application_id"), table_name="government_queries")
    op.drop_table("government_queries")
    op.drop_index(op.f("ix_application_timeline_events_id"), table_name="application_timeline_events")
    op.drop_index(op.f("ix_application_timeline_events_event_type"), table_name="application_timeline_events")
    op.drop_index(op.f("ix_application_timeline_events_application_id"), table_name="application_timeline_events")
    op.drop_index(op.f("ix_application_timeline_events_actor_user_id"), table_name="application_timeline_events")
    op.drop_table("application_timeline_events")
