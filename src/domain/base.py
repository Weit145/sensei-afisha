import datetime
import uuid
from dataclasses import dataclass, field


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


@dataclass(slots=True, kw_only=True)
class Entity:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = field(default_factory=utc_now)
