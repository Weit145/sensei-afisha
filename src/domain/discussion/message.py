import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.base import Entity
from src.domain.err import InvalidDataError

MAX_MESSAGE_LENGTH = 2000


@dataclass(slots=True, kw_only=True)
class Message(Entity):
    afisha_id: uuid.UUID
    author_id: uuid.UUID
    text: str
    deleted_at: datetime | None = None
    nickname: str = ""

    def __post_init__(self) -> None:
        self.text = self.text.strip()
        if not self.text or len(self.text) > MAX_MESSAGE_LENGTH:
            raise InvalidDataError(
                f"Message text must contain 1 to {MAX_MESSAGE_LENGTH} characters"
            )
