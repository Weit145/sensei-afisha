from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.user import UserModel


class SQLAlchemyUserRepository:
    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> UserModel | None:
        return await session.scalar(
            select(UserModel).where(UserModel.username == username)
        )

    async def create_user(self, session: AsyncSession, user: UserModel) -> UserModel:
        session.add(user)
        await session.flush()
        return user
