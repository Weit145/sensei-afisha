import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.afisha import AfishaUpdate
from src.repositories.storage.models.afisha import AfishaModel


class AfishaRepository(Protocol):
    async def create_afisha(
        self,
        session: AsyncSession,
        afisha:AfishaModel,
        venues:list[uuid.UUID]
    )->None:
        ...

    async def update_afisha(
        self,
        session: AsyncSession,
        afisha:AfishaModel,
        afisha_id: uuid.UUID,
    )->AfishaModel:
        ...

    async def patch_afisha(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
        changes: AfishaUpdate,
    ) -> AfishaModel:
        ...

    async def delete_afisha(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
    ) -> None:
        ...

    async def list_afisha(
        self,
        session: AsyncSession,
        page: int,
        page_size: int,
        search: str | None,
    ) -> tuple[list[AfishaModel], int]:
        ...

    async def read_afisha(
        self,
        session: AsyncSession,
        afisha_id: uuid.UUID,
    ) -> AfishaModel:
        ...
