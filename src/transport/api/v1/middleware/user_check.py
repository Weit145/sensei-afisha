import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.user import UserRole
from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.schemas.auth import CurrentUser
from src.usecase.auth.auth_service import InvalidTokenError, auth_service

logger = logging.getLogger(__name__)

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
) -> CurrentUser:
    try:
        if credentials is None:
            raise InvalidTokenError
        user = await auth_service.get_current_user(credentials.credentials, session)
        return CurrentUser(user_id=user.id, username=user.username, role=user.role)

    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "invalid token"}},
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        ) from exc


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
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "admin role required"}},
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "user role required"}},
        )

    return current_user
