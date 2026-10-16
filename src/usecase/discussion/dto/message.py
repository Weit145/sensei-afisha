import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.discussion.message import Message

DEFAULT_MESSAGE_LIMIT = 50
MAX_MESSAGE_LIMIT = 100


@dataclass(slots=True, frozen=True)
class MessageCursor:
    afisha_id: uuid.UUID
    created_at: datetime
    id: uuid.UUID


@dataclass(slots=True)
class MessageListResult:
    items: list[Message]
    next_cursor: MessageCursor | None = None
    has_more: bool = False
