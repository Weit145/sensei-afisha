from sqlalchemy import Column, ForeignKey, Table, Uuid

from ..base import Base

user_afisha_follows = Table(
    "user_afisha_follows",
    Base.metadata,
    Column(
        "user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "afisha_id",
        Uuid(as_uuid=True),
        ForeignKey("afisha.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
