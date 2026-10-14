import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

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
