from dataclasses import dataclass
from datetime import datetime

from src.domain.user import User


@dataclass(slots=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_at: datetime
