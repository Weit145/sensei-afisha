"""Create concert discussion messages.

Revision ID: 20261014_03
Revises: 20261014_02
"""

import sqlalchemy as sa
from alembic import op

revision = "20261014_03"
down_revision = "20261014_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discussion_messages",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "afisha_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("afisha.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "char_length(text) BETWEEN 1 AND 2000 AND text ~ '[^[:space:]]'",
            name="check_discussion_message_text",
        ),
    )
    op.create_index(
        "ix_discussion_messages_history",
        "discussion_messages",
        ["afisha_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_discussion_messages_history", table_name="discussion_messages")
    op.drop_table("discussion_messages")
