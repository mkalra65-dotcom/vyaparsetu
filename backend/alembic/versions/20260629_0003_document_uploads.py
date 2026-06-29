"""Document upload metadata

Revision ID: 20260629_0003
Revises: 20260629_0002
Create Date: 2026-06-29 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_0003"
down_revision: str | None = "20260629_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("original_filename", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("stored_filename", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("file_path", sa.String(length=1024), nullable=True))
    op.add_column("documents", sa.Column("mime_type", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("file_size", sa.BigInteger(), nullable=True))
    op.add_column("documents", sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True))

    op.execute("UPDATE documents SET original_filename = file_name WHERE original_filename IS NULL")
    op.execute("UPDATE documents SET stored_filename = file_name WHERE stored_filename IS NULL")
    op.execute("UPDATE documents SET file_path = file_url WHERE file_path IS NULL")
    op.execute("UPDATE documents SET mime_type = 'application/octet-stream' WHERE mime_type IS NULL")
    op.execute("UPDATE documents SET file_size = 0 WHERE file_size IS NULL")
    op.execute(
        """
        UPDATE documents
        SET uploaded_by_user_id = applications.owner_id
        FROM applications
        WHERE documents.application_id = applications.id
          AND documents.uploaded_by_user_id IS NULL
        """
    )

    op.alter_column("documents", "document_type", nullable=False)
    op.alter_column("documents", "original_filename", nullable=False)
    op.alter_column("documents", "stored_filename", nullable=False)
    op.alter_column("documents", "file_path", nullable=False)
    op.alter_column("documents", "mime_type", nullable=False)
    op.alter_column("documents", "file_size", nullable=False)
    op.alter_column("documents", "uploaded_by_user_id", nullable=False)
    op.create_foreign_key(
        "fk_documents_uploaded_by_user_id_users",
        "documents",
        "users",
        ["uploaded_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_column("documents", "file_url")
    op.drop_column("documents", "file_name")


def downgrade() -> None:
    op.add_column("documents", sa.Column("file_name", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("file_url", sa.String(length=1024), nullable=True))
    op.execute("UPDATE documents SET file_name = original_filename WHERE file_name IS NULL")
    op.execute("UPDATE documents SET file_url = file_path WHERE file_url IS NULL")
    op.alter_column("documents", "file_name", nullable=False)
    op.alter_column("documents", "file_url", nullable=False)

    op.drop_constraint("fk_documents_uploaded_by_user_id_users", "documents", type_="foreignkey")
    op.drop_column("documents", "uploaded_by_user_id")
    op.drop_column("documents", "file_size")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "file_path")
    op.drop_column("documents", "stored_filename")
    op.drop_column("documents", "original_filename")
    op.alter_column("documents", "document_type", nullable=True)
