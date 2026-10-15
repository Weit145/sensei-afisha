
import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class AfishaReviewsModel(Base):
    __tablename__ = "afisha_reviews"

    __table_args__ = (
        CheckConstraint(
            "reviews_count >= 0",
            name="ck_reviews_count",
        ),
        CheckConstraint(
            "rating_sum >= reviews_count "
            "AND rating_sum <= reviews_count * 5",
            name="ck_rating_sum",
        ),
    )

    afisha_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("afisha.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    reviews: Mapped[list["ReviewsModel"]] = relationship(
        "ReviewsModel",
        back_populates="afisha_reviews",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    rating_sum: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    reviews_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    @property
    def avg_rating(self) -> float:
        if self.reviews_count == 0:
            return 0.0

        return self.rating_sum / self.reviews_count
