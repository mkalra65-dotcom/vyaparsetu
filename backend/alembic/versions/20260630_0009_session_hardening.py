"""Session hardening

Revision ID: 20260630_0009
Revises: 20260629_0008
Create Date: 2026-06-30 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0009"
down_revision: str | None = "20260629_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("last_logout_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("users", "token_version", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "last_logout_at")
    op.drop_column("users", "token_version")
