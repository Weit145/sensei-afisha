import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha import Venue, VenueUpdate
from src.repositories.storage.map.afisha import (
    map_venue_to_domain as map_to_domain,
    map_venue_to_model as map_to_model,
)
from src.repositories.storage.postgres.afisha import SQLAlchemyVenueRepository
from src.usecase.afisha.dto import VenueListResult
from src.usecase.port.afisha import VenueRepository


class VenueService:
    def __init__(self, repo: VenueRepository) -> None:
        self.repo = repo

    async def create_venue(
        self,
        venue: Venue,
        session: AsyncSession,
    ) -> Venue:
        try:
            db_result = await self.repo.create_venue(session, map_to_model(venue))
            result = map_to_domain(db_result)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def update_venue(
        self,
        venue: Venue,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> Venue:
        db_venue = map_to_model(venue)
        db_venue.id = venue_id
        try:
            db_result = await self.repo.update_venue(session, db_venue, venue_id)
            result = map_to_domain(db_result)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def patch_venue(
        self,
        venue: VenueUpdate,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> Venue:
        try:
            db_result = await self.repo.patch_venue(session, venue_id, venue)
            result = map_to_domain(db_result)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def delete_venue(
        self,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> None:
        try:
            await self.repo.delete_venue(session, venue_id)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    async def list_venue(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> VenueListResult:
        db_venues, total = await self.repo.list_venue(session, page, page_size, search)
        return VenueListResult(
            items=[map_to_domain(db_venue) for db_venue in db_venues],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def read_venue(
        self,
        venue_id: uuid.UUID,
        session: AsyncSession,
    ) -> Venue:
        db_venue = await self.repo.read_venue(session, venue_id)
        return map_to_domain(db_venue)


venue_service = VenueService(SQLAlchemyVenueRepository())
