import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserModel(Base):
    __tablename__ = "users"

    # name: Mapped[str] = mapped_column(String(100), nullable=False)
    # ip: Mapped[str] = mapped_column(String(45), nullable=False)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(10))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    reviews: Mapped[list["ReviewModel"]] = relationship(
    "ReviewModel",
    back_populates="author",
    passive_deletes=True,
)