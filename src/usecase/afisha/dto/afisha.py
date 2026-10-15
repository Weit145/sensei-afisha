import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.afisha import Afisha


@dataclass
class AfishaListItem:
    afisha: Afisha
    venue_names: list[str]
    cover_file_name: str | None


@dataclass
class AfishaListResult:
    items: list[AfishaListItem]
    total: int
    page: int
    page_size: int


@dataclass
class AfishaImageItem:
    id: uuid.UUID
    file_name: str
    is_cover: bool
    position: int


@dataclass
class AfishaDetailResult:
    afisha: Afisha
    created_at: datetime
    updated_at: datetime
    images: list[AfishaImageItem] = field(default_factory=list)
