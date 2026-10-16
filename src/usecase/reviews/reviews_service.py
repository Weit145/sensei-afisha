import uuid
from datetime import timezone

from src.domain.afisha.afisha import AfishaStatus
from src.domain.base import utc_now
from src.domain.err import InvalidDataError, NotFoundError, UnauthorizedError
from src.domain.reviews.afisha_reviews import AfishaReviews
from src.domain.reviews.reviews import Review
from src.usecase.port.reviews.reviews_repositories import (
    AfishaReviewReader,
    ReviewsRepository,
)


class ReviewsService:
    def __init__(
        self,
        repo: ReviewsRepository,
        afisha_reader: AfishaReviewReader,
    ) -> None:
        self.repo = repo
        self.afisha_reader = afisha_reader

    @staticmethod
    def _require_author(author_id: uuid.UUID | None) -> uuid.UUID:
        if author_id is None:
            raise UnauthorizedError("Для этого действия нужно авторизоваться")
        return author_id

    async def _require_afisha(self, afisha_id: uuid.UUID) -> None:
        info = await self.afisha_reader.get_review_info(afisha_id)
        if info is None:
            raise NotFoundError("Афиша не найдена")

    async def _require_finished_afisha(self, afisha_id: uuid.UUID) -> None:
        info = await self.afisha_reader.get_review_info(afisha_id)
        if info is None:
            raise NotFoundError("Афиша не найдена")
        if info.status != AfishaStatus.PUBLISHED:
            raise InvalidDataError("Для отменённого мероприятия отзывы недоступны")
        if info.ends_at.tzinfo is None or info.ends_at.utcoffset() is None:
            raise InvalidDataError("Дата окончания афиши должна содержать часовой пояс")
        if info.ends_at.astimezone(timezone.utc) > utc_now():
            raise InvalidDataError("Оставить отзыв можно после окончания мероприятия")

    async def get_stats_by_afisha_ids(
        self, afisha_ids: list[uuid.UUID]
    ) -> list[AfishaReviews]:
        return await self.repo.get_stats_by_afisha_ids(afisha_ids)

    async def get_reviews_by_afisha_id(
        self,
        afisha_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[AfishaReviews, list[Review]]:
        if not 1 <= limit <= 100:
            raise InvalidDataError("limit должен быть от 1 до 100")
        if offset < 0:
            raise InvalidDataError("offset не может быть отрицательным")
        await self._require_afisha(afisha_id)
        result = await self.repo.get_reviews_by_afisha_id(
            afisha_id=afisha_id, limit=limit, offset=offset
        )
        if result is None:
            return AfishaReviews(afisha_id=afisha_id), []
        return result

    async def create_review(
        self,
        *,
        afisha_id: uuid.UUID,
        author_id: uuid.UUID | None,
        rating: int,
        text: str,
    ) -> Review:
        author_id = self._require_author(author_id)
        await self._require_finished_afisha(afisha_id)
        try:
            review = Review(
                afisha_id=afisha_id,
                author_id=author_id,
                rating=rating,
                text=text,
            )
        except ValueError as exc:
            raise InvalidDataError(str(exc)) from exc
        return await self.repo.create_review(review)

    async def update_review(
        self,
        *,
        afisha_id: uuid.UUID,
        review_id: uuid.UUID,
        author_id: uuid.UUID | None,
        rating: int | None = None,
        text: str | None = None,
    ) -> Review:
        author_id = self._require_author(author_id)
        if rating is None and text is None:
            raise InvalidDataError("Укажите оценку или текст")
        if rating is not None:
            try:
                Review.validate_rating(rating)
            except ValueError as exc:
                raise InvalidDataError(str(exc)) from exc
        if text is not None:
            try:
                Review.validate_text(text)
            except ValueError as exc:
                raise InvalidDataError(str(exc)) from exc
        try:
            updated = await self.repo.update_review(
                afisha_id=afisha_id,
                review_id=review_id,
                author_id=author_id,
                rating=rating,
                text=text,
            )
        except ValueError as exc:
            raise InvalidDataError(str(exc)) from exc
        if updated is None:
            raise NotFoundError("Отзыв не найден или принадлежит другому пользователю")
        return updated

    async def delete_review(
        self,
        *,
        afisha_id: uuid.UUID,
        review_id: uuid.UUID,
        author_id: uuid.UUID | None,
    ) -> None:
        author_id = self._require_author(author_id)
        deleted = await self.repo.delete_review(
            afisha_id=afisha_id, review_id=review_id, author_id=author_id
        )
        if not deleted:
            raise NotFoundError("Отзыв не найден или принадлежит другому пользователю")
