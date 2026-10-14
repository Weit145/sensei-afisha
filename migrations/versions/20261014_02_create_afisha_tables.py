"""Create afisha, venues, images, and their association table.

Revision ID: 20261014_02
Revises: 20261011_01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261014_02"
down_revision = "20261011_01"
branch_labels = None
depends_on = None

afisha_status = postgresql.ENUM(
    "published", "cancelled", name="afisha_status", create_type=False
)


def upgrade() -> None:
    afisha_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "afisha",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("age_limit", sa.Integer(), nullable=True),
        sa.Column("status", afisha_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="check_afisha_dates"),
        sa.CheckConstraint("age_limit BETWEEN 0 AND 18", name="check_afisha_age_limit"),
    )

    op.create_table(
        "venues",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name="check_venue_latitude"),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name="check_venue_longitude"),
    )

    op.create_table(
        "afisha_venues",
        sa.Column("afisha_id", sa.Uuid(as_uuid=True), sa.ForeignKey("afisha.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("venue_id", sa.Uuid(as_uuid=True), sa.ForeignKey("venues.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "afisha_images",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("afisha_id", sa.Uuid(as_uuid=True), sa.ForeignKey("afisha.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("is_cover", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("afisha_images")
    op.drop_table("afisha_venues")
    op.drop_table("venues")
    op.drop_table("afisha")
    afisha_status.drop(op.get_bind(), checkfirst=True)
