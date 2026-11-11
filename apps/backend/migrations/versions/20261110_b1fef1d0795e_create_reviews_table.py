"""create reviews table

Revision ID: b1fef1d0795e
Revises: eefa62e04909
Create Date: 2026-11-10 19:32:02.145788

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1fef1d0795e"
down_revision: str | Sequence[str] | None = "eefa62e04909"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name=op.f("ck_reviews_rating_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
        sa.UniqueConstraint("content_hash", name=op.f("uq_reviews_content_hash")),
    )
    op.create_index("ix_reviews_reviewed_at_id", "reviews", ["reviewed_at", "id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reviews_reviewed_at_id", table_name="reviews")
    op.drop_table("reviews")
