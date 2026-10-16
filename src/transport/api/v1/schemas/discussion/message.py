import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints

from src.domain.discussion.message import MAX_MESSAGE_LENGTH


class CreateMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_LENGTH
        ),
    ]


class MessageResponse(BaseModel):
    id: uuid.UUID
    afisha_id: uuid.UUID
    author_id: uuid.UUID
    text: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None
    has_more: bool


class MessageCursorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    afisha_id: uuid.UUID
    created_at: AwareDatetime
    id: uuid.UUID
