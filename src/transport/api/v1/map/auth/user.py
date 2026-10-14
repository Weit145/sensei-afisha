from src.domain.user import User
from src.transport.api.v1.schemas.auth import UserResponse


def map_to_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, role=user.role)
