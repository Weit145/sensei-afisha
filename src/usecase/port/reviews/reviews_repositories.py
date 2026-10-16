import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.afisha.afisha import AfishaStatus
from src.domain.reviews.afisha_reviews import AfishaReviews
from src.domain.reviews.reviews import Review


@dataclass(frozen=True, slots=True)
class AfishaReviewInfo:
    ends_at: datetime
    status: AfishaStatus


class AfishaReviewReader(Protocol):
    async def get_review_info(
        self, afisha_id: uuid.UUID
    ) -> AfishaReviewInfo | None: ...


class ReviewsRepository(Protocol):
    async def get_stats_by_afisha_ids(
        self, afisha_ids: list[uuid.UUID]
    ) -> list[AfishaReviews]: ...

    async def get_reviews_by_afisha_id(
        self, afisha_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[AfishaReviews, list[Review]] | None: ...

    async def create_review(self, review: Review) -> Review: ...

    async def update_review(
        self,
        afisha_id: uuid.UUID,
        review_id: uuid.UUID,
        author_id: uuid.UUID,
        *,
        rating: int | None = None,
        text: str | None = None,
    ) -> Review | None: ...

    async def delete_review(
        self, afisha_id: uuid.UUID, review_id: uuid.UUID, author_id: uuid.UUID
    ) -> bool: ...
