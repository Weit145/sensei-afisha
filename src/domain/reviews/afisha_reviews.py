
import uuid
from dataclasses import dataclass

from src.domain.base import Entity


@dataclass(slots=True, kw_only=True)
class AfishaReviews(Entity):
    afisha_id: uuid.UUID
    rating_sum: int = 0
    reviews_count: int = 0

    def __post_init__(self) -> None:
        if self.reviews_count < 0:
            raise ValueError(
                "Количество отзывов не может быть отрицательным"
            )

        if not 0 <= self.rating_sum <= self.reviews_count * 5:
            raise ValueError("Некорректная сумма рейтингов")

    @property
    def avg_rating(self) -> float:
        if self.reviews_count == 0:
            return 0.0

        return self.rating_sum / self.reviews_count

    def add_review(self, rating: int) -> None:
        if not 1 <= rating <= 5:
            raise ValueError("Рейтинг должен быть от 1 до 5")

        self.rating_sum += rating
        self.reviews_count += 1