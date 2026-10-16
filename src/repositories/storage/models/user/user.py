from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from ..afisha import AfishaModel
    from ..reviews.reviews import ReviewsModel

from ..base import Base
from .association import user_afisha_follows


class UserModel(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(10))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    followed_afishas: Mapped[list["AfishaModel"]] = relationship(
        secondary=user_afisha_follows,
        back_populates="followers",
    )

    reviews: Mapped[list["ReviewsModel"]] = relationship(
        "ReviewsModel",
        back_populates="author",
        passive_deletes=True,
    )
