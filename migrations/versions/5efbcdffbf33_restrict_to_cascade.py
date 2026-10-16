"""Cascade discussion messages when an afisha is deleted.

Revision ID: 5efbcdffbf33
Revises: 99b73000c91d
Create Date: 2026-10-16 21:59:47.797462
"""
from alembic import op

revision: str = "5efbcdffbf33"
down_revision: str = "99b73000c91d"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.drop_constraint(
        "discussion_messages_afisha_id_fkey",
        "discussion_messages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "discussion_messages_afisha_id_fkey",
        "discussion_messages",
        "afisha",
        ["afisha_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "discussion_messages_afisha_id_fkey",
        "discussion_messages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "discussion_messages_afisha_id_fkey",
        "discussion_messages",
        "afisha",
        ["afisha_id"],
        ["id"],
        ondelete="RESTRICT",
    )
