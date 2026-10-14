from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .association import afisha_venues

if TYPE_CHECKING:
    from .afisha import AfishaModel


class VenueModel(Base):
    __tablename__ = "venues"

    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="check_venue_latitude",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="check_venue_longitude",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    afishas: Mapped[list["AfishaModel"]] = relationship(
        secondary=afisha_venues,
        back_populates="venues",
    )
