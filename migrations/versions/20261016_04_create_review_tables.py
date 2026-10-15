
    
  
"""Create afisha review statistics and individual reviews.

Revision ID: 20261016_04
Revises: 20261014_03
"""

import sqlalchemy as sa
from alembic import op

revision = "20261016_04"
down_revision = "20261014_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "afisha_reviews",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "afisha_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("afisha.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating_sum", sa.Integer(), nullable=False),
        sa.Column("reviews_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("afisha_id"),
        sa.CheckConstraint("reviews_count >= 0", name="ck_reviews_count"),
        sa.CheckConstraint(
            "rating_sum >= reviews_count AND rating_sum <= reviews_count * 5",
            name="ck_rating_sum",
        ),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "afisha_reviews_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("afisha_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
        sa.UniqueConstraint(
            "author_id",
            "afisha_reviews_id",
            name="uq_reviews_author_afisha_reviews",
        ),
    )


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("afisha_reviews")

