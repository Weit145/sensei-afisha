from sqlalchemy import Column, ForeignKey, Table, Uuid

from ..base import Base

afisha_participation= Table(
    "afisha_participation",
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
    ),
)
