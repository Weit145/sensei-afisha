from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class CurrentUser(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    user_id: UUID
    role: UserRole
