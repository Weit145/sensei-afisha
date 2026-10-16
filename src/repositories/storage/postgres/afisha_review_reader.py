import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.afisha.afisha import AfishaModel
from src.usecase.port.reviews.reviews_repositories import AfishaReviewInfo


class SqlAlchemyAfishaReviewReader:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_review_info(
        self, afisha_id: uuid.UUID
    ) -> AfishaReviewInfo | None:
        row = (
            await self.session.execute(
                select(AfishaModel.ends_at, AfishaModel.status).where(
                    AfishaModel.id == afisha_id
                )
            )
        ).one_or_none()
        if row is None:
            return None
        return AfishaReviewInfo(ends_at=row.ends_at, status=row.status)
