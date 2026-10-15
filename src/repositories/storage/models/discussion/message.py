import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repositories.storage.models.base import Base

if TYPE_CHECKING:
    from ..afisha import AfishaModel

class MessageModel(Base):
    __tablename__ = "discussion_messages"
    __table_args__ = (
        CheckConstraint(
            "char_length(text) BETWEEN 1 AND 2000 AND text ~ '[^[:space:]]'",
            name="check_discussion_message_text",
        ),
        Index("ix_discussion_messages_history", "afisha_id", "created_at", "id"),
    )

    afisha_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("afisha.id", ondelete="RESTRICT"),
        nullable=False,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    afisha: Mapped["AfishaModel"] = relationship(back_populates="messages")
