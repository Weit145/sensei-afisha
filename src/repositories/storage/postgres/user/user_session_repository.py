from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.storage.models.user import UserSessionModel


class SQLAlchemyUserSessionRepository:
    async def create_session(
        self, session: AsyncSession, user_session: UserSessionModel
    ) -> UserSessionModel:
        session.add(user_session)
        await session.flush()
        return user_session

    async def get_by_id(
        self, session: AsyncSession, session_id: UUID, *, for_update: bool = False
    ) -> UserSessionModel | None:
        query = select(UserSessionModel).where(UserSessionModel.id == session_id)
        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await session.scalar(query)
