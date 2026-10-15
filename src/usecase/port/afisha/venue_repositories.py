import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha import VenueUpdate
from src.repositories.storage.models.afisha import VenueModel


class VenueRepository(Protocol):
    async def create_venue(
        self,
        session: AsyncSession,
        venue: VenueModel,
    ) -> VenueModel:
        ...

    async def update_venue(
        self,
        session: AsyncSession,
        venue: VenueModel,
        venue_id: uuid.UUID,
    ) -> VenueModel:
        ...

    async def patch_venue(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
        changes: VenueUpdate,
    ) -> VenueModel:
        ...

    async def delete_venue(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
    ) -> None:
        ...

    async def list_venue(
        self,
        session: AsyncSession,
        page: int,
        page_size: int,
        search: str | None,
    ) -> tuple[list[VenueModel], int]:
        ...

    async def read_venue(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
    ) -> VenueModel:
        ...
