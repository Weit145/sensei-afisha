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
import uuid
from ..base import Base


class ReviewsModel(Base):
    __tablename__ = "reviews"

    __table_args__ = CheckConstraint("rating BETWEEN 1 AND 5"),
    UniqueConstraint("author_id", "afisha_id", name="uq_reviews_author_afisha")

    afisha_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("afisha.id", ondelete="CASCADE"),
        nullable=False,)

    afisha: Mapped["AfishaModel"] = relationship(
        "AfishaModel",
        back_populates="reviews",
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),)

    author: Mapped["UserModel | None"] = relationship(
        "UserModel",
        back_populates="reviews",
    )


    rating: Mapped[int] = mapped_column(Integer, nullable = False)
    text: Mapped[str] = mapped_column(Text, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)