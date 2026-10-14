from src.domain.discussion.message import Message
from src.repositories.storage.models.discussion.message import MessageModel


def map_to_model(message: Message) -> MessageModel:
    return MessageModel(
        id=message.id,
        afisha_id=message.afisha_id,
        author_id=message.author_id,
        text=message.text,
        created_at=message.created_at,
        deleted_at=message.deleted_at,
    )


def map_to_domain(model: MessageModel) -> Message:
    return Message(
        id=model.id,
        afisha_id=model.afisha_id,
        author_id=model.author_id,
        text=model.text,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )
