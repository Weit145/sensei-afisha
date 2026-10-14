from uuid import UUID

from pydantic import BaseModel
from pydantic.config import ConfigDict

from src.domain.user import UserRole


class CurrentUser(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
    )

    user_id: UUID
    role: UserRole
