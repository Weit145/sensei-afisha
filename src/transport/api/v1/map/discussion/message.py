import uuid

from src.domain.discussion.message import Message
from src.transport.api.v1.schemas.discussion.message import (
    CreateMessage,
    MessageListResponse,
    MessageResponse,
)
from src.usecase.discussion.dto.message import MessageListResult


def map_to_domain(
    data: CreateMessage, afisha_id: uuid.UUID, author_id: uuid.UUID
) -> Message:
    return Message(afisha_id=afisha_id, author_id=author_id, text=data.text)


def map_to_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        afisha_id=message.afisha_id,
        author_id=message.author_id,
        text=message.text if message.deleted_at is None else "Сообщение удалено",
        created_at=message.created_at,
    )


def map_to_list_response(result: MessageListResult) -> MessageListResponse:
    return MessageListResponse(items=[map_to_response(item) for item in result.items])
