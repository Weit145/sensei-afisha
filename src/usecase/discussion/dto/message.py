from dataclasses import dataclass

from src.domain.discussion.message import Message


@dataclass(slots=True)
class MessageListResult:
    items: list[Message]
