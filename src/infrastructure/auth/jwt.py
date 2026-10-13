import logging
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from src.core.config import settings

logger = logging.getLogger(__name__)

def create_token (user_id: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(UTC) + expires_delta
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload

    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise ValueError("Invalid token") from exc
