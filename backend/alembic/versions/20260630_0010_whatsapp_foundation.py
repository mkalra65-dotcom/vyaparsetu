"""WhatsApp foundation

Revision ID: 20260630_0010
Revises: 20260630_0009
Create Date: 2026-06-30 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0010"
down_revision: str | None = "20260630_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("wa_id", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("consent_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_contacts_id"), "whatsapp_contacts", ["id"], unique=False)
    op.create_index(op.f("ix_whatsapp_contacts_phone_number"), "whatsapp_contacts", ["phone_number"], unique=True)
    op.create_index(op.f("ix_whatsapp_contacts_user_id"), "whatsapp_contacts", ["user_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_contacts_wa_id"), "whatsapp_contacts", ["wa_id"], unique=True)

    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("selected_service_type", sa.String(length=50), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["whatsapp_contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_sessions_application_id"), "conversation_sessions", ["application_id"], unique=False)
    op.create_index(op.f("ix_conversation_sessions_contact_id"), "conversation_sessions", ["contact_id"], unique=False)
    op.create_index(op.f("ix_conversation_sessions_id"), "conversation_sessions", ["id"], unique=False)

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("message_type", sa.String(length=50), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["whatsapp_contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["conversation_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_messages_application_id"), "conversation_messages", ["application_id"], unique=False)
    op.create_index(op.f("ix_conversation_messages_contact_id"), "conversation_messages", ["contact_id"], unique=False)
    op.create_index(op.f("ix_conversation_messages_id"), "conversation_messages", ["id"], unique=False)
    op.create_index(op.f("ix_conversation_messages_provider_message_id"), "conversation_messages", ["provider_message_id"], unique=False)
    op.create_index(op.f("ix_conversation_messages_session_id"), "conversation_messages", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_conversation_messages_session_id"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_provider_message_id"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_id"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_contact_id"), table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_application_id"), table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index(op.f("ix_conversation_sessions_id"), table_name="conversation_sessions")
    op.drop_index(op.f("ix_conversation_sessions_contact_id"), table_name="conversation_sessions")
    op.drop_index(op.f("ix_conversation_sessions_application_id"), table_name="conversation_sessions")
    op.drop_table("conversation_sessions")
    op.drop_index(op.f("ix_whatsapp_contacts_wa_id"), table_name="whatsapp_contacts")
    op.drop_index(op.f("ix_whatsapp_contacts_user_id"), table_name="whatsapp_contacts")
    op.drop_index(op.f("ix_whatsapp_contacts_phone_number"), table_name="whatsapp_contacts")
    op.drop_index(op.f("ix_whatsapp_contacts_id"), table_name="whatsapp_contacts")
    op.drop_table("whatsapp_contacts")
