import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.afisha import AfishaStatsModel


class SQLAlchemyAfishaStatsRepository:
    async def get_by_afisha_ids(
        self,
        session: AsyncSession,
        afisha_ids: list[uuid.UUID],
    ) -> list[AfishaStatsModel]:
        if not afisha_ids:
            return []
        rows = await session.scalars(
            select(AfishaStatsModel).where(AfishaStatsModel.afisha_id.in_(afisha_ids))
        )
        return list(rows.all())

    async def get_by_afisha_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID
    ) -> AfishaStatsModel | None:
        return await session.scalar(
            select(AfishaStatsModel).where(AfishaStatsModel.afisha_id == afisha_id)
        )
