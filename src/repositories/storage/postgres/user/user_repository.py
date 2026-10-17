import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.user import UserModel, user_afisha_follows


class SQLAlchemyUserRepository:
    async def get_followed_afisha_ids(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> list[uuid.UUID]:
        return list(await session.scalars(
            select(user_afisha_follows.c.afisha_id)
            .where(user_afisha_follows.c.user_id == user_id)
            .order_by(user_afisha_follows.c.afisha_id)
        ))

    async def get_by_username(
        self,
        session: AsyncSession,
        username: str
    ) -> UserModel | None:
        return await session.scalar(
            select(UserModel).where(UserModel.username == username)
        )

    async def create_user(
        self,
        session: AsyncSession,
        user: UserModel
    ) -> UserModel:
        session.add(user)
        await session.flush()
        return user

    async def get_by_user_id(
        self,
        session: AsyncSession,
        user_id: uuid.UUID
    ) -> UserModel | None:
        return await session.scalar(
            select(UserModel).where(UserModel.id == user_id)
        )
