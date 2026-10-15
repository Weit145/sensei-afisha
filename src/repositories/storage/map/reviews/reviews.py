
from src.domain.reviews.reviews import Review
from src.repositories.models.reviews import ReviewsModel


class ReviewMapper:

    @staticmethod
    def to_domain(model: ReviewsModel) -> Review:
        return Review(
            id=model.id,
            author_id=model.author_id,
            afisha_id=model.afisha_id,
            rating=model.rating,
            text=model.text,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Review) -> ReviewsModel:
        return ReviewsModel(
            id=entity.id,
            author_id=entity.author_id,
            afisha_id=entity.afisha_id,
            rating=entity.rating,
            text=entity.text,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
