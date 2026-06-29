"""Document intelligence extraction

Revision ID: 20260629_0006
Revises: 20260629_0005
Create Date: 2026-06-29 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260629_0006"
down_revision: str | None = "20260629_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("health_score", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("ai_review_summary", sa.Text(), nullable=True))

    op.create_table(
        "document_extractions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("extracted_json", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("validation_warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_extractions_document_id"), "document_extractions", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_extractions_id"), "document_extractions", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_extractions_id"), table_name="document_extractions")
    op.drop_index(op.f("ix_document_extractions_document_id"), table_name="document_extractions")
    op.drop_table("document_extractions")
    op.drop_column("applications", "ai_review_summary")
    op.drop_column("applications", "health_score")
