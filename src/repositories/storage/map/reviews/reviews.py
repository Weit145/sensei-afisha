
import uuid

from src.domain.reviews.reviews import Review
from src.repositories.storage.models.reviews.reviews import ReviewsModel


class ReviewMapper:

    @staticmethod
    def to_domain(
        model: ReviewsModel,
        afisha_id: uuid.UUID,
        nickname: str | None = None,
    ) -> Review:
        return Review(
            id=model.id,
            author_id=model.author_id,
            nickname=nickname,
            afisha_id=afisha_id,
            rating=model.rating,
            text=model.text,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Review,
        afisha_reviews_id: uuid.UUID,
    ) -> ReviewsModel:
        return ReviewsModel(
            id=entity.id,
            afisha_reviews_id=afisha_reviews_id,
            author_id=entity.author_id,
            rating=entity.rating,
            text=entity.text,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(
        entity: Review,
        model: ReviewsModel,
    ) -> None:
        model.rating = entity.rating
        model.text = entity.text
        model.updated_at = entity.updated_at
