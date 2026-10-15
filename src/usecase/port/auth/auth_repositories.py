from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.user import UserModel


class UserRepository(Protocol):
    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> UserModel | None: ...

    async def create_user(
        self, session: AsyncSession, user: UserModel
    ) -> UserModel: ...
