from dataclasses import dataclass

from src.domain.base import Entity


@dataclass(slots=True)
class User(Entity):
    name: str
    ip: str
