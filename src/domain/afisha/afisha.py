import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from src.domain.base import Entity, utc_now


class AfishaStatus(StrEnum):
    PUBLISHED = "published"
    CANCELLED = "cancelled"


@dataclass(slots=True, kw_only=True)
class Afisha(Entity):
    title: str
    description: str| None = None
    short_description: str | None = None

    starts_at: datetime
    ends_at: datetime

    venue_ids: list[uuid.UUID]

    age_limit: int | None = None

    status: AfishaStatus = AfishaStatus.PUBLISHED

    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if self.ends_at <= self.starts_at:
            raise ValueError(
                "Дата окончания должна быть позже начала"
            )

        if not self.venue_ids:
            raise ValueError(
                "У мероприятия должна быть хотя бы одна площадка"
            )

        if self.age_limit is not None and self.age_limit not in (0, 6, 12, 16, 18):
                raise ValueError("Некорректное возрастное ограничение")

        if self.updated_at is not None and self.updated_at<=self.created_at:
            raise ValueError(
                "Дата обновление не может быть раньше или равна созданию"
            )

    def cancel(self) -> None:
        self.status = AfishaStatus.CANCELLED

@dataclass(slots=True, kw_only=True)
class AfishaUpdate(Entity):
    title: str| None = None
    description: str| None = None
    short_description: str | None = None

    starts_at: datetime| None = None
    ends_at: datetime| None = None

    venue_ids: list[uuid.UUID]| None = None

    age_limit: int | None = None

    status: AfishaStatus | None = None

    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if self.ends_at is not None and self.starts_at is not None and self.ends_at <= self.starts_at:
            raise ValueError(
                "Дата окончания должна быть позже начала"
            )

        if self.age_limit is not None and self.age_limit not in (0, 6, 12, 16, 18):
                raise ValueError("Некорректное возрастное ограничение")

        if self.updated_at is not None and self.updated_at<=self.created_at:
            raise ValueError(
                "Дата обновление не может быть раньше или равна созданию"
            )
