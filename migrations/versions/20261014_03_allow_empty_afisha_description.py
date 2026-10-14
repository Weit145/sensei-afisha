"""Allow afisha without a description.

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
    op.alter_column("afisha", "description", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE afisha SET description = '' WHERE description IS NULL")
    op.alter_column("afisha", "description", existing_type=sa.Text(), nullable=False)
