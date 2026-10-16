import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.afisha import AfishaStatsModel


class AfishaStatsRepository(Protocol):
    async def get_by_afisha_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID
    ) -> AfishaStatsModel | None:
        ...
