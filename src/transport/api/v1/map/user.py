from ipaddress import ip_address

from src.domain.user import User
from src.transport.api.v1.schemas.user import CreateUser, UserResponse


def map_to_domain(data: CreateUser) -> User:
    return User(name=data.name, ip=str(data.ip))


def map_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        ip=ip_address(user.ip),
        created_at=user.created_at,
    )
