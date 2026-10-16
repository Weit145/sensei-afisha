from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.user import UserSessionModel


class UserSessionRepository(Protocol):
    async def create_session(
        self, session: AsyncSession, user_session: UserSessionModel
    ) -> UserSessionModel: ...

    async def get_by_id(
        self, session: AsyncSession, session_id: UUID, *, for_update: bool = False
    ) -> UserSessionModel | None: ...
