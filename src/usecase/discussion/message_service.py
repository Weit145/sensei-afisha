import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.discussion.message import Message
from src.domain.err import NotFoundError, UnauthorizedError
from src.usecase.discussion.dto.message import MessageListResult
from src.usecase.port.discussion.message_repositories import MessageRepository


class MessageService:
    def __init__(self, repo: MessageRepository) -> None:
        self.repo = repo

    async def _require_afisha(
        self, afisha_id: uuid.UUID, session: AsyncSession
    ) -> None:
        if not await self.repo.afisha_exists(afisha_id, session):
            raise NotFoundError("Concert not found")

    async def _require_author(
        self, author_id: uuid.UUID, session: AsyncSession
    ) -> None:
        if not await self.repo.author_exists(author_id, session):
            raise UnauthorizedError("Token user no longer exists")

    async def create_message(self, message: Message, session: AsyncSession) -> Message:
        await self._require_author(message.author_id, session)
        await self._require_afisha(message.afisha_id, session)
        try:
            created = await self.repo.create_message(message, session)
            await self.repo.commit(session)
        except IntegrityError:
            # A concert or author may have been removed after the existence checks.
            await session.rollback()
            await self._require_author(message.author_id, session)
            await self._require_afisha(message.afisha_id, session)
            raise
        return created

    async def list_messages(
        self, afisha_id: uuid.UUID, session: AsyncSession
    ) -> MessageListResult:
        await self._require_afisha(afisha_id, session)
        return MessageListResult(
            items=await self.repo.list_messages(afisha_id, session)
        )
