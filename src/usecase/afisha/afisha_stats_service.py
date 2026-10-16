import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import NotFoundError
from src.repositories.storage.postgres.afisha import (
    SQLAlchemyAfishaStatsRepository,
)
from src.usecase.afisha.dto import AfishaStatsResult
from src.usecase.port.afisha import AfishaStatsRepository

logger = logging.getLogger(__name__)

class AfishaStatsService:
    def __init__(
        self,
        stats_repo: AfishaStatsRepository
    ) -> None:
        self.stats_repo = stats_repo

    async def get_stats_by_afisha_id(
        self,
        afisha_id: uuid.UUID,
        session: AsyncSession,
    ) -> AfishaStatsResult:
        stats = await self.stats_repo.get_by_afisha_id(
            session=session,
            afisha_id=afisha_id,
        )

        if stats is None:
            raise NotFoundError("Статистика афиши не найдена")

        return AfishaStatsResult(
            afisha_id=stats.afisha_id,
            followers_count=stats.followers_count,
        )

afisha_stats_service = AfishaStatsService(
    stats_repo=SQLAlchemyAfishaStatsRepository(),
)
