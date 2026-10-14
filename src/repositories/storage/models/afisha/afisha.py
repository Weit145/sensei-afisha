from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.afisha import AfishaStatus

from ..base import Base
from .association import afisha_venues

if TYPE_CHECKING:
    from .img import AfishaImageModel
    from .venue import VenueModel


class AfishaModel(Base):
    __tablename__ = "afisha"

    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at",
            name="check_afisha_dates",
        ),
        CheckConstraint(
            "age_limit BETWEEN 0 AND 18",
            name="check_afisha_age_limit",
        ),
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    short_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    age_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[AfishaStatus] = mapped_column(
        Enum(
            AfishaStatus,
            name="afisha_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=AfishaStatus.PUBLISHED,
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

    venues: Mapped[list["VenueModel"]] = relationship(
        secondary=afisha_venues,
        back_populates="afishas",
    )
    images: Mapped[list["AfishaImageModel"]] = relationship(
        back_populates="afisha",
        cascade="all, delete-orphan",
    )
