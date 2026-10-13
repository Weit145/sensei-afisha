from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from uuid import UUID

from pydantic import BaseModel, Field, IPvAnyAddress, field_validator


class CreateUser(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    ip: IPvAnyAddress

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class UserResponse(BaseModel):
    id: UUID
    name: str
    ip: IPv4Address | IPv6Address
    created_at: datetime
