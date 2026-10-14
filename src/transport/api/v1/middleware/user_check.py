
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.user import UserRole
from src.infrastructure.jwt import decode_token
from src.transport.api.v1.schemas.auth import CurrentUser

logger = logging.getLogger(__name__)

bearer = HTTPBearer()

def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer),
    ],
) -> CurrentUser:
    try:
        payload = decode_token(credentials.credentials)
        return CurrentUser.model_validate(payload)

    except ValueError as exc:
        logger.warning("HTTP_401_UNAUTHORIZED, invalid token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "invalid token"}}
        )

CurrentUserDep = Annotated[
    CurrentUser,
    Depends(get_current_user),
]


def require_admin(
    current_user: CurrentUserDep,
) -> CurrentUser:
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "HTTP_403_FORBIDDEN, admin role required, user_id: %s, user_role: %s",
            current_user.user_id,
            current_user.role,
        )
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = {"error": {"code": "FORBIDDEN", "message": "admin role required"}},
        )
    return current_user

def require_user(
    current_user: CurrentUserDep,
) -> CurrentUser:
    if current_user.role != UserRole.USER:
        logger.warning(
            "HTTP_403_FORBIDDEN, user role required, user_id: %s, user_role: %s",
            current_user.user_id,
            current_user.role,
        )
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = {"error": {"code": "FORBIDDEN", 'message': "user role required"}},
        )

    return current_user
