from sqlalchemy import Column, ForeignKey, Table, Uuid

from ..base import Base

afisha_venues = Table(
    "afisha_venues",
    Base.metadata,
    Column(
        "afisha_id",
        Uuid(as_uuid=True),
        ForeignKey("afisha.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "venue_id",
        Uuid(as_uuid=True),
        ForeignKey("venues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
