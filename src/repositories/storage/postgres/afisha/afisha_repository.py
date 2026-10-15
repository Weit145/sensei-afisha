import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.afisha import AfishaUpdate
from src.domain.err import InvalidDataError, NotFoundError
from src.repositories.storage.models.afisha import AfishaModel, VenueModel


class SQLAlchemyAfishaRepository:
    async def create_afisha(
        self,
        session: AsyncSession,
        afisha: AfishaModel,
        venues: list[uuid.UUID],
    ) -> None:
        afisha.venues = await self._load_venues(session, venues)
        session.add(afisha)
        await session.flush()

    async def update_afisha(
        self,
        session: AsyncSession,
        afisha: AfishaModel,
        venues: list[uuid.UUID],
    ) -> AfishaModel:
        current = await self._get_by_id(session, afisha.id)
        current.venues = await self._load_venues(session, venues)
        for field in (
            "title",
            "description",
            "short_description",
            "starts_at",
            "ends_at",
            "age_limit",
            "status",
            "updated_at",
        ):
            setattr(current, field, getattr(afisha, field))
        await session.flush()
        return current

    async def patch_afisha(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        changes: AfishaUpdate,
    ) -> AfishaModel:
        afisha = await self._get_by_id(session, afisha_id)
        for field in (
            "title",
            "description",
            "short_description",
            "starts_at",
            "ends_at",
            "age_limit",
            "status",
        ):
            value = getattr(changes, field)
            if value is not None:
                setattr(afisha, field, value)

        if changes.venue_ids is not None:
            afisha.venues = await self._load_venues(session, changes.venue_ids)

        if afisha.ends_at <= afisha.starts_at:
            raise InvalidDataError("Дата окончания должна быть позже начала")
        afisha.updated_at = changes.updated_at
        await session.flush()
        return afisha

    async def delete_afisha(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
    ) -> None:
        afisha = await self._get_by_id(session, afisha_id)
        await session.delete(afisha)

    async def list_afisha(
        self,
        session: AsyncSession,
        page: int,
        page_size: int,
        search: str | None,
    ) -> tuple[list[AfishaModel], int]:
        criteria = None
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            criteria = or_(
                AfishaModel.title.ilike(pattern),
                AfishaModel.description.ilike(pattern),
                AfishaModel.short_description.ilike(pattern),
            )

        count_query = select(func.count(AfishaModel.id))
        list_query = select(AfishaModel).options(
            selectinload(AfishaModel.venues),
            selectinload(AfishaModel.images),
        )
        if criteria is not None:
            count_query = count_query.where(criteria)
            list_query = list_query.where(criteria)

        total = await session.scalar(count_query) or 0
        list_query = (
            list_query.order_by(AfishaModel.starts_at, AfishaModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.scalars(list_query)).unique().all()
        return list(items), total

    async def read_afisha(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
    ) -> AfishaModel:
        return await self._get_by_id(session, afisha_id)

    async def _get_by_id(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
    ) -> AfishaModel:
        query = (
            select(AfishaModel)
            .options(
                selectinload(AfishaModel.venues),
                selectinload(AfishaModel.images),
            )
            .where(AfishaModel.id == afisha_id)
        )
        afisha = await session.scalar(query)
        if afisha is None:
            raise NotFoundError("Afisha not found")
        return afisha

    async def _load_venues(
        self,
        session: AsyncSession,
        venue_ids: list[uuid.UUID],
    ) -> list[VenueModel]:
        unique_ids = list(dict.fromkeys(venue_ids))
        if not unique_ids:
            raise InvalidDataError("У мероприятия должна быть хотя бы одна площадка")
        models = (
            await session.scalars(select(VenueModel).where(VenueModel.id.in_(unique_ids)))
        ).all()
        by_id = {venue.id: venue for venue in models}
        if len(by_id) != len(unique_ids):
            raise NotFoundError("Одна или несколько площадок не найдены")
        return [by_id[venue_id] for venue_id in unique_ids]
