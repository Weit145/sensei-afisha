import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .afisha import AfishaModel


class AfishaImageModel(Base):
    __tablename__ = "afisha_images"

    afisha_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("afisha.id", ondelete="CASCADE"),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    is_cover: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    afisha: Mapped["AfishaModel"] = relationship(back_populates="images")
