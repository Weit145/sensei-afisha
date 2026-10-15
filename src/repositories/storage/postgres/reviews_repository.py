
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.reviews.reviews import Review
from src.domain.reviews.afisha_reviews import AfishaReviews

from src.repositories.storage.models.reviews.reviews import ReviewsModel
from src.repositories.storage.models.reviews.afisha_reviews import (
    AfishaReviewsModel,
)

from src.repositories.storage.map.reviews.reviews import ReviewMapper
from src.repositories.storage.map.reviews.afisha_reviews import (
    AfishaReviewsMapper,
)


class AfishaReviewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 1. Получить статистику нескольких афиш
    async def get_stats_by_afisha_ids(
        self,
        afisha_ids: list[uuid.UUID],
    ) -> list[AfishaReviews]:

        if not afisha_ids:
            return []

        stmt = (
            select(AfishaReviewsModel)
            .where(AfishaReviewsModel.afisha_id.in_(afisha_ids))
        )

        result = await self.session.scalars(stmt)

        return [
            AfishaReviewsMapper.to_domain(model)
            for model in result.all()
        ]

    # 2. Получить статистику и страницу отзывов
    async def get_reviews_by_afisha_id(
        self,
        afisha_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[AfishaReviews, list[Review]] | None:

        if not 1 <= limit <= 100:
            raise ValueError("limit должен быть от 1 до 100")

        if offset < 0:
            raise ValueError("offset не может быть отрицательным")

        stats_stmt = (
            select(AfishaReviewsModel)
            .where(AfishaReviewsModel.afisha_id == afisha_id)
        )

        stats_model = await self.session.scalar(stats_stmt)

        if stats_model is None:
            return None

        reviews_stmt = (
            select(ReviewsModel)
            .where(
                ReviewsModel.afisha_reviews_id == stats_model.id
            )
            .order_by(
                ReviewsModel.created_at.desc(),
                ReviewsModel.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        reviews_result = await self.session.scalars(reviews_stmt)

        stats = AfishaReviewsMapper.to_domain(stats_model)

        reviews = [
            ReviewMapper.to_domain(
                model=review_model,
                afisha_id=afisha_id,
            )
            for review_model in reviews_result.all()
        ]

        return stats, reviews

    # 3. Создать отзыв
    async def create_review(
        self,
        review: Review,
    ) -> Review:

        if review.author_id is None:
            raise ValueError("Для создания отзыва нужен автор")

        stats_stmt = (
            select(AfishaReviewsModel)
            .where(
                AfishaReviewsModel.afisha_id == review.afisha_id
            )
            .with_for_update()
        )

        stats_model = await self.session.scalar(stats_stmt)

        if stats_model is None:
            raise ValueError("Статистика афиши не найдена")

        review_model = ReviewMapper.to_model(
            entity=review,
            afisha_reviews_id=stats_model.id,
        )

        self.session.add(review_model)

        stats_model.rating_sum += review.rating
        stats_model.reviews_count += 1

        await self.session.flush()

        return review

    # 4. Удалить свой отзыв
    async def delete_review(
        self,
        afisha_id: uuid.UUID,
        review_id: uuid.UUID,
        author_id: uuid.UUID,
    ) -> bool:

        stats_stmt = (
            select(AfishaReviewsModel)
            .where(AfishaReviewsModel.afisha_id == afisha_id)
            .with_for_update()
        )

        stats_model = await self.session.scalar(stats_stmt)

        if stats_model is None:
            return False

        review_stmt = (
            select(ReviewsModel)
            .where(
                ReviewsModel.id == review_id,
                ReviewsModel.afisha_reviews_id == stats_model.id,
                ReviewsModel.author_id == author_id,
            )
        )

        review_model = await self.session.scalar(review_stmt)

        if review_model is None:
            return False

        stats_model.rating_sum -= review_model.rating
        stats_model.reviews_count -= 1

        await self.session.delete(review_model)
        await self.session.flush()

        return True
