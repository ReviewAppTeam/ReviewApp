"""enable pgvector

Revision ID: eefa62e04909
Revises:
Create Date: 2026-11-10 18:57:28.191643

"""

from collections.abc import Sequence

from alembic import op

revision: str = "eefa62e04909"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
