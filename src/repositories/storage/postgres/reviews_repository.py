import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.base import utc_now
from src.domain.reviews.afisha_reviews import AfishaReviews
from src.domain.reviews.reviews import Review
from src.repositories.storage.map.reviews.afisha_reviews import AfishaReviewsMapper
from src.repositories.storage.map.reviews.reviews import ReviewMapper
from src.repositories.storage.models.reviews.afisha_reviews import AfishaReviewsModel
from src.repositories.storage.models.reviews.reviews import ReviewsModel


class AfishaReviewsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_stats_by_afisha_ids(
        self, afisha_ids: list[uuid.UUID]
    ) -> list[AfishaReviews]:
        if not afisha_ids:
            return []
        rows = await self.session.scalars(
            select(AfishaReviewsModel).where(
                AfishaReviewsModel.afisha_id.in_(afisha_ids)
            )
        )
        return [AfishaReviewsMapper.to_domain(row) for row in rows.all()]

    async def get_reviews_by_afisha_id(
        self, afisha_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[AfishaReviews, list[Review]] | None:
        if not 1 <= limit <= 100:
            raise ValueError("limit должен быть от 1 до 100")
        if offset < 0:
            raise ValueError("offset не может быть отрицательным")

        stats_model = await self.session.scalar(
            select(AfishaReviewsModel).where(
                AfishaReviewsModel.afisha_id == afisha_id
            )
        )
        if stats_model is None:
            return None

        rows = await self.session.scalars(
            select(ReviewsModel)
            .where(ReviewsModel.afisha_reviews_id == stats_model.id)
            .order_by(ReviewsModel.created_at.desc(), ReviewsModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        stats = AfishaReviewsMapper.to_domain(stats_model)
        reviews = [
            ReviewMapper.to_domain(row, afisha_id=afisha_id)
            for row in rows.all()
        ]
        return stats, reviews

    async def _lock_stats(self, afisha_id: uuid.UUID) -> AfishaReviewsModel | None:
        return await self.session.scalar(
            select(AfishaReviewsModel)
            .where(AfishaReviewsModel.afisha_id == afisha_id)
            .with_for_update()
        )

    async def create_review(self, review: Review) -> Review:
        if review.author_id is None:
            raise ValueError("Для создания отзыва нужен автор")

        await self.session.execute(
            insert(AfishaReviewsModel)
            .values(
                id=uuid.uuid4(),
                afisha_id=review.afisha_id,
                rating_sum=0,
                reviews_count=0,
            )
            .on_conflict_do_nothing(index_elements=[AfishaReviewsModel.afisha_id])
        )
        stats = await self._lock_stats(review.afisha_id)
        if stats is None:
            raise RuntimeError("Не удалось создать статистику отзывов")

        model = ReviewMapper.to_model(
            entity=review, afisha_reviews_id=stats.id
        )
        self.session.add(model)
        stats.rating_sum += review.rating
        stats.reviews_count += 1
        await self.session.flush()
        return ReviewMapper.to_domain(model, afisha_id=review.afisha_id)

    async def update_review(
        self,
        afisha_id: uuid.UUID,
        review_id: uuid.UUID,
        author_id: uuid.UUID,
        *,
        rating: int | None = None,
        text: str | None = None,
    ) -> Review | None:
        stats = await self._lock_stats(afisha_id)
        if stats is None:
            return None

        model = await self.session.scalar(
            select(ReviewsModel).where(
                ReviewsModel.id == review_id,
                ReviewsModel.afisha_reviews_id == stats.id,
                ReviewsModel.author_id == author_id,
            )
        )
        if model is None:
            return None

        if rating is not None:
            Review.validate_rating(rating)
            stats.rating_sum += rating - model.rating
            model.rating = rating
        if text is not None:
            Review.validate_text(text)
            model.text = text.strip()
        if rating is not None or text is not None:
            model.updated_at = utc_now()
        await self.session.flush()
        return ReviewMapper.to_domain(model, afisha_id=afisha_id)

    async def delete_review(
        self, afisha_id: uuid.UUID, review_id: uuid.UUID, author_id: uuid.UUID
    ) -> bool:
        stats = await self._lock_stats(afisha_id)
        if stats is None:
            return False
        model = await self.session.scalar(
            select(ReviewsModel).where(
                ReviewsModel.id == review_id,
                ReviewsModel.afisha_reviews_id == stats.id,
                ReviewsModel.author_id == author_id,
            )
        )
        if model is None:
            return False

        stats.rating_sum -= model.rating
        stats.reviews_count -= 1
        await self.session.delete(model)
        await self.session.flush()
        return True
