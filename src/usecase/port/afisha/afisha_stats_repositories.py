import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.afisha import AfishaStatsModel


class AfishaStatsRepository(Protocol):
    async def get_by_afisha_ids(
        self,
        session: AsyncSession,
        afisha_ids: list[uuid.UUID],
    ) -> list[AfishaStatsModel]:
        ...

    async def get_by_afisha_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID
    ) -> AfishaStatsModel | None:
        ...
