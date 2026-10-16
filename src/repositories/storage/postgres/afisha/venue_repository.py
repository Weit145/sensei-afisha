import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha import VenueUpdate
from src.domain.err import InvalidDataError, NotFoundError
from src.repositories.storage.models.afisha import VenueModel


class SQLAlchemyVenueRepository:
    async def create_venue(
        self,
        session: AsyncSession,
        venue: VenueModel,
    ) -> VenueModel:
        session.add(venue)
        await session.flush()
        return venue

    async def update_venue(
        self,
        session: AsyncSession,
        venue: VenueModel,
        venue_id: uuid.UUID,
    ) -> VenueModel:
        current = await self._get_by_id(session, venue_id)
        for field in ("name", "city", "address", "latitude", "longitude"):
            setattr(current, field, getattr(venue, field))
        await session.flush()
        return current

    async def patch_venue(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
        changes: VenueUpdate,
    ) -> VenueModel:
        venue = await self._get_by_id(session, venue_id)
        for field in ("name", "city", "address", "latitude", "longitude"):
            value = getattr(changes, field)
            if value is not None:
                setattr(venue, field, value)

        if not venue.name.strip() or not venue.city.strip() or not venue.address.strip():
            raise InvalidDataError("Название, город и адрес не могут быть пустыми")
        await session.flush()
        return venue

    async def delete_venue(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
    ) -> None:
        venue = await self._get_by_id(session, venue_id)
        await session.delete(venue)

    async def list_venue(
        self,
        session: AsyncSession,
        page: int,
        page_size: int,
        search: str | None,
    ) -> tuple[list[VenueModel], int]:
        criteria = None
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            criteria = or_(
                VenueModel.name.ilike(pattern),
                VenueModel.city.ilike(pattern),
                VenueModel.address.ilike(pattern),
            )

        count_query = select(func.count(VenueModel.id))
        list_query = select(VenueModel)
        if criteria is not None:
            count_query = count_query.where(criteria)
            list_query = list_query.where(criteria)

        total = await session.scalar(count_query) or 0
        list_query = (
            list_query.order_by(VenueModel.name, VenueModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.scalars(list_query)).all()
        return list(items), total

    async def read_venue(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
    ) -> VenueModel:
        return await self._get_by_id(session, venue_id)

    async def _get_by_id(
        self,
        session: AsyncSession,
        venue_id: uuid.UUID,
    ) -> VenueModel:
        venue = await session.get(VenueModel, venue_id)
        if venue is None:
            raise NotFoundError("Площадка не найдена")
        return venue
