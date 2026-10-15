import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class ReviewsModel(Base):
    __tablename__ = "reviews"

    __table_args__ = (
    CheckConstraint(
        "rating BETWEEN 1 AND 5",
        name="ck_reviews_rating",
    ),
    UniqueConstraint(
        "author_id",
        "afisha_reviews_id",
        name="uq_reviews_author_afisha_reviews",
    ),
    )
    
    afisha_reviews_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("afisha_reviews.id", ondelete="CASCADE"),
        nullable=False,)

    afisha_reviews: Mapped["AfishaReviewsModel"] = relationship(
    "AfishaReviewsModel",
    back_populates="reviews",
)

    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable = True)

    author: Mapped["UserModel | None"] = relationship(
        "UserModel",
        back_populates="reviews",
    )


    rating: Mapped[int] = mapped_column(Integer, nullable = False)
    text: Mapped[str] = mapped_column(Text, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)