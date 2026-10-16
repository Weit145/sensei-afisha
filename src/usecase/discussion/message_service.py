import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.discussion.message import Message
from src.domain.err import InvalidDataError, NotFoundError, UnauthorizedError
from src.usecase.discussion.dto.message import (
    DEFAULT_MESSAGE_LIMIT,
    MAX_MESSAGE_LIMIT,
    MessageCursor,
    MessageListResult,
)
from src.usecase.port.discussion.message_repositories import MessageRepository
from src.usecase.port.notifier import Notifier

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(
        self, repo: MessageRepository, notifier: Notifier | None = None
    ) -> None:
        self.repo = repo
        self.notifier = notifier

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

    async def create_message(
        self, message: Message, session: AsyncSession, nickname: str
    ) -> Message:
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
        if self.notifier is not None:
            try:
                await self.notifier.SendAboutNewDescussionMessages(
                    created.afisha_id, created.text, created.author_id, nickname
                )
            except Exception:
                # The message is already committed; a failed notification must not
                # turn a successful POST into an error and cause a duplicate retry.
                logger.exception(
                    "Could not notify subscribers about message %s", created.id
                )
        return created

    async def list_messages(
        self,
        afisha_id: uuid.UUID,
        session: AsyncSession,
        *,
        limit: int = DEFAULT_MESSAGE_LIMIT,
        before: MessageCursor | None = None,
    ) -> MessageListResult:
        if not 1 <= limit <= MAX_MESSAGE_LIMIT:
            raise InvalidDataError(
                f"Message limit must be between 1 and {MAX_MESSAGE_LIMIT}"
            )
        if before is not None and before.afisha_id != afisha_id:
            raise InvalidDataError("Message cursor belongs to another concert")
        await self._require_afisha(afisha_id, session)
        # Fetch one extra row to detect an older page without counting the history.
        messages = await self.repo.list_messages(
            afisha_id, session, limit=limit + 1, before=before
        )
        has_more = len(messages) > limit
        items = list(reversed(messages[:limit]))
        next_cursor = None
        if has_more:
            oldest = items[0]
            next_cursor = MessageCursor(
                afisha_id=afisha_id, created_at=oldest.created_at, id=oldest.id
            )
        return MessageListResult(
            items=items, next_cursor=next_cursor, has_more=has_more
        )
