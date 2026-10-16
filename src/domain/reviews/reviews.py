
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.base import Entity, utc_now


@dataclass(kw_only=True)
class Review(Entity):
    author_id: uuid.UUID | None
    afisha_id: uuid.UUID
    rating: int
    text: str
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.validate_rating(self.rating)
        self.validate_text(self.text)
        self.text = self.text.strip()

    @staticmethod
    def validate_rating(rating: int) -> None:
        if not 1 <= rating <= 5:
            raise ValueError("Рейтинг должен быть от 1 до 5")

    @staticmethod
    def validate_text(text: str) -> None:
        if not text.strip():
            raise ValueError("Отзыв должен содержать текст")

    def change_rating(self, rating: int) -> None:
        self.validate_rating(rating)
        self.rating = rating
        self.updated_at = utc_now()

    def edit_text(self, text: str) -> None:
        self.validate_text(text)
        self.text = text.strip()
        self.updated_at = utc_now()
