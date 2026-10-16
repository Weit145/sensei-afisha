import sqlalchemy as sa
from alembic import op

revision = "20261016_01"
down_revision = "20261015_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_afisha_follows",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "afisha_id",
            sa.Uuid(),
            sa.ForeignKey("afisha.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_user_afisha_follows_afisha_id", "user_afisha_follows", ["afisha_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_afisha_follows_afisha_id", table_name="user_afisha_follows")
    op.drop_table("user_afisha_follows")
