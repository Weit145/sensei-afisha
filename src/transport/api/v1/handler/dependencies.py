
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.auth.jwt import decode_token

logger = logging.getLogger(__name__)

bearer = HTTPBearer()

def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer),
    ],
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
        return {"user_id": payload["user_id"], "role": payload["role"]}

    except ValueError as exc:
        logger.warning("HTTP_401_UNAUTHORIZED, invalid token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "invalid token"}}
        )

def require_admin(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
) -> dict:
    if current_user["role"] != "admin":
        logger.warning("HTTP_403_FORBIDDEN, admin role required, user_id: %s, user_role: %s", current_user["user_id"], current_user["role"])
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = {"error": {"code": "FORBIDDEN", "message": "admin role required"}},
        )
    return current_user

def require_user(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
) -> dict:
    if current_user["role"] != "user":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = {"error": {"code": "FORBIDDEN", 'message': "user role required"}},
        )

    return current_user
