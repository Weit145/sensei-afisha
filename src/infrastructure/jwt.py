import logging
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from src.core.config import settings

logger = logging.getLogger(__name__)

def create_token (user_id: str, role: str) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(UTC) + expires_delta
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload

    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise ValueError("Invalid token") from exc
