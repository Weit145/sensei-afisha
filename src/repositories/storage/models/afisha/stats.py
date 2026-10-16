import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .afisha import AfishaModel


class AfishaStatsModel(Base):
    __tablename__ = "afisha_stats"
    __table_args__ = (
        CheckConstraint(
            "followers_count >= 0",
            name="check_afisha_followers_count"
        ),
    )

    id = None

    afisha_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("afisha.id", ondelete="CASCADE"),
        primary_key=True
    )
    followers_count: Mapped[int] = mapped_column(
        BigInteger,
        server_default=text("0")
    )
    afisha: Mapped["AfishaModel"] = relationship(
        back_populates="stats",
        viewonly=True
    )
