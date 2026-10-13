from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.user import User


class Repository(Protocol):
    async def create_user(self, user: User, session: AsyncSession) -> User: ...
    async def commit(self, session: AsyncSession) -> None: ...
