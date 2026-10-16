from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain.user import UserRole


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class UserResponse(BaseModel):
    id: UUID
    username: str
    role: UserRole


class UserContactsResponse(BaseModel):
    tg_url: str | None
    vk_url: str | None


class UpdateUserContactsRequest(BaseModel):
    tg_url: str | None = Field(
        default=None,
        max_length=255,
        examples=["https://t.me/username"],
    )
    vk_url: str | None = Field(
        default=None,
        max_length=255,
        examples=["https://vk.com/username"],
    )

    @field_validator("tg_url", "vk_url", mode="before")
    @classmethod
    def normalize_url(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("tg_url")
    @classmethod
    def validate_tg_url(cls, value: str | None) -> str | None:
        return cls.validate_social_url(value, {"t.me", "telegram.me"}, "Telegram")

    @field_validator("vk_url")
    @classmethod
    def validate_vk_url(cls, value: str | None) -> str | None:
        return cls.validate_social_url(value, {"vk.com"}, "VK")

    @model_validator(mode="after")
    def require_contact(self) -> "UpdateUserContactsRequest":
        if not self.model_fields_set:
            raise ValueError("Передайте хотя бы один контакт")
        return self

    @staticmethod
    def validate_social_url(
        value: str | None,
        allowed_hosts: set[str],
        service_name: str,
    ) -> str | None:
        if value is None:
            return None
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or not parsed.path.strip("/")
        ):
            raise ValueError(f"Укажите корректную HTTPS-ссылку на профиль {service_name}")
        return value


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(UserResponse):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    user_id: UUID
    username: str
    role: UserRole
    tg_url: str | None = None
    vk_url: str | None = None
