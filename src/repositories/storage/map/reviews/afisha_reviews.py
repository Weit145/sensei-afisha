
from src.domain.reviews.afisha_reviews import AfishaReviews
from src.repositories.storage.models.reviews.afisha_reviews import (
    AfishaReviewsModel,
)


class AfishaReviewsMapper:

    @staticmethod
    def to_domain(
        model: AfishaReviewsModel,
    ) -> AfishaReviews:
        return AfishaReviews(
            id=model.id,
            afisha_id=model.afisha_id,
            rating_sum=model.rating_sum,
            reviews_count=model.reviews_count,
        )

    @staticmethod
    def to_model(
        entity: AfishaReviews,
    ) -> AfishaReviewsModel:
        return AfishaReviewsModel(
            id=entity.id,
            afisha_id=entity.afisha_id,
            rating_sum=entity.rating_sum,
            reviews_count=entity.reviews_count,
        )

    @staticmethod
    def update_model(
        entity: AfishaReviews,
        model: AfishaReviewsModel,
    ) -> None:
        model.rating_sum = entity.rating_sum
        model.reviews_count = entity.reviews_count
