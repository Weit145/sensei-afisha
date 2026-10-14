import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.discussion.message import Message


class MessageRepository(Protocol):
    async def afisha_exists(
        self, afisha_id: uuid.UUID, session: AsyncSession
    ) -> bool: ...
    async def author_exists(
        self, author_id: uuid.UUID, session: AsyncSession
    ) -> bool: ...
    async def create_message(
        self, message: Message, session: AsyncSession
    ) -> Message: ...
    async def list_messages(
        self, afisha_id: uuid.UUID, session: AsyncSession
    ) -> list[Message]: ...
    async def commit(self, session: AsyncSession) -> None: ...
