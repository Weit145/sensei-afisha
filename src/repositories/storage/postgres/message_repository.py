import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.discussion.message import Message
from src.repositories.storage.map.discussion.message import map_to_domain, map_to_model
from src.repositories.storage.models import AfishaModel, MessageModel, UserModel


class SQLAlchemyMessageRepository:
    async def afisha_exists(self, afisha_id: uuid.UUID, session: AsyncSession) -> bool:
        return bool(
            await session.scalar(
                select(
                    select(AfishaModel.id).where(AfishaModel.id == afisha_id).exists()
                )
            )
        )

    async def author_exists(self, author_id: uuid.UUID, session: AsyncSession) -> bool:
        # Existence checks do not load profile data.
        return bool(
            await session.scalar(
                select(select(UserModel.id).where(UserModel.id == author_id).exists())
            )
        )

    async def create_message(self, message: Message, session: AsyncSession) -> Message:
        model = map_to_model(message)
        session.add(model)
        await session.flush()
        return map_to_domain(model)

    async def list_messages(
        self, afisha_id: uuid.UUID, session: AsyncSession
    ) -> list[Message]:
        models = await session.scalars(
            select(MessageModel)
            .where(MessageModel.afisha_id == afisha_id)
            .order_by(MessageModel.created_at, MessageModel.id)
        )
        return [map_to_domain(model) for model in models]

    async def commit(self, session: AsyncSession) -> None:
        await session.commit()
