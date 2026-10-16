from src.domain.user import User
from src.transport.api.v1.schemas.auth import (
    AuthResponse,
    UserContactsResponse,
    UserResponse,
)
from src.usecase.auth.dto.auth import AuthResult


def map_to_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, role=user.role)


def map_to_contacts_response(user: User) -> UserContactsResponse:
    return UserContactsResponse(tg_url=user.tg_url, vk_url=user.vk_url)


def map_to_auth_response(result: AuthResult) -> AuthResponse:
    return AuthResponse(
        id=result.user.id,
        username=result.user.username,
        role=result.user.role,
        access_token=result.access_token,
        expires_in=result.expires_in,
    )
