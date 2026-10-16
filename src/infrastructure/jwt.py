from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Literal
from uuid import UUID, uuid4

from jose import JWTError, jwt

from src.core.config import settings
from src.domain.user import UserRole


def create_token(user_id: UUID, role: UserRole, session_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "role": role.value,
        "sid": str(session_id),
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def create_refresh_token(user_id: UUID, session_id: UUID, expires_at: datetime) -> str:
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": datetime.now(UTC),
        "exp": expires_at,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def decode_token(
    token: str, token_type: Literal["access", "refresh"] = "access"
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
                "require_jti": True,
            },
        )
        if payload.get("type") != token_type:
            raise ValueError("Invalid token type")
        for key in ("sub", "sid", "jti"):
            value = payload.get(key)
            if not isinstance(value, str):
                raise TypeError("Invalid token claims")
            UUID(value)
        return payload
    except (JWTError, ValueError, TypeError) as exc:
        raise ValueError("Invalid token") from exc
