"""Add social contacts to users.

Revision ID: 20261017_01
Revises: 5efbcdffbf33
"""

import sqlalchemy as sa
from alembic import op

revision = "20261017_01"
down_revision = "5efbcdffbf33"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("tg_url", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("vk_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "vk_url")
    op.drop_column("users", "tg_url")
