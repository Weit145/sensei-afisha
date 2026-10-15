"""Replace legacy user fields with authentication fields.

Revision ID: 20261014_01
Revises: 20261011_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20261014_01"
down_revision = "20261011_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=30), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=10),
            nullable=False,
            server_default="user",
        ),
    )
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
    )

    op.execute(
        "UPDATE users "
        "SET username = 'legacy_' || "
        "translate(rtrim(encode(uuid_send(id), 'base64'), '='), '+/', '-_') "
        "WHERE username IS NULL",
    )
    op.alter_column("users", "username", nullable=False)
    op.alter_column("users", "role", server_default=None)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.drop_column("users", "ip")
    op.drop_column("users", "name")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "name", sa.String(length=100), nullable=False, server_default="legacy"
        ),
    )
    op.add_column(
        "users",
        sa.Column("ip", sa.String(length=45), nullable=False, server_default="0.0.0.0"),
    )

    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "role")
    op.drop_column("users", "username")

    op.alter_column("users", "name", server_default=None)
    op.alter_column("users", "ip", server_default=None)
