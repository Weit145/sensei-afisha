from dataclasses import dataclass
from enum import StrEnum

from src.domain.base import Entity


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


@dataclass(slots=True, kw_only=True)
class User(Entity):
    username: str
    role: UserRole = UserRole.USER
    hashed_password: str | None = None

    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        if not isinstance(self.role, UserRole):
            raise TypeError("Некорректная роль")
