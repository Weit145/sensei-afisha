import base64
import uuid

from src.domain.discussion.message import Message
from src.transport.api.v1.schemas.discussion.message import (
    CreateMessage,
    MessageCursorPayload,
    MessageListResponse,
    MessageResponse,
)
from src.usecase.discussion.dto.message import MessageCursor, MessageListResult


def encode_cursor(cursor: MessageCursor) -> str:
    payload = MessageCursorPayload(
        afisha_id=cursor.afisha_id, created_at=cursor.created_at, id=cursor.id
    )
    return (
        base64.urlsafe_b64encode(payload.model_dump_json().encode())
        .decode()
        .rstrip("=")
    )


def decode_cursor(value: str, afisha_id: uuid.UUID) -> MessageCursor:
    payload = MessageCursorPayload.model_validate_json(
        base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    )
    if payload.afisha_id != afisha_id:
        raise ValueError("Message cursor belongs to another concert")
    return MessageCursor(
        afisha_id=payload.afisha_id, created_at=payload.created_at, id=payload.id
    )


def map_to_domain(
    data: CreateMessage, afisha_id: uuid.UUID, author_id: uuid.UUID
) -> Message:
    return Message(afisha_id=afisha_id, author_id=author_id, text=data.text)


def map_to_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        afisha_id=message.afisha_id,
        author_id=message.author_id,
        nickname=message.nickname,
        text=message.text if message.deleted_at is None else "Сообщение удалено",
        created_at=message.created_at,
    )


def map_to_list_response(result: MessageListResult) -> MessageListResponse:
    return MessageListResponse(
        items=[map_to_response(item) for item in result.items],
        next_cursor=encode_cursor(result.next_cursor)
        if result.next_cursor is not None
        else None,
        has_more=result.has_more,
    )
