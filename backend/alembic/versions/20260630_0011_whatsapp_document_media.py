"""WhatsApp document media metadata

Revision ID: 20260630_0011
Revises: 20260630_0010
Create Date: 2026-06-30 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0011"
down_revision: str | None = "20260630_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("provider_media_id", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("source_channel", sa.String(length=50), nullable=True))
    op.execute("UPDATE documents SET source_channel = 'web' WHERE source_channel IS NULL")
    op.alter_column("documents", "source_channel", nullable=False)
    op.create_index(op.f("ix_documents_provider_media_id"), "documents", ["provider_media_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_provider_media_id"), table_name="documents")
    op.drop_column("documents", "source_channel")
    op.drop_column("documents", "provider_media_id")
