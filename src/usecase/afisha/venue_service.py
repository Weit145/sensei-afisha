import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha.venue import Venue, VenueUpdate
from src.usecase.afisha.dto.venue import VenueListResult
from src.usecase.port.afisha.venue_repositories import VenueRepository

logger = logging.getLogger(__name__)


class VenueService:
    def __init__(self, repo: VenueRepository | None = None) -> None:
        self.repo = repo


    async def create_venue(
        self,
        venue: Venue,
        session: AsyncSession,
    ) -> Venue:
        return venue

    async def update_venue(
        self,
        venue: Venue,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> Venue:
        return venue

    async def patch_venue(
        self,
        venue: VenueUpdate,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> Venue:
        raise NotImplementedError("Обновление афиши ещё не реализовано")

    async def delete_venue(
        self,
        venue_id: uuid.UUID,
        session: AsyncSession,
    )-> None:
        return

    async def list_venue(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> VenueListResult:
        return VenueListResult(items=[], total=0, page=page, page_size=page_size)

    async def read_venue(
        self,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> Venue:
        raise NotImplementedError("Чтение афиши ещё не реализовано")


venue_service = VenueService()
