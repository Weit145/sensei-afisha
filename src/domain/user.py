from dataclasses import dataclass
from enum import StrEnum

from src.domain.base import Entity


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"

@dataclass(slots=True)
class User(Entity):
    role: UserRole = UserRole.USER
    hashed_password: str | None = None

    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN
