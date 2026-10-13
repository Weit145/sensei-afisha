from dataclasses import dataclass
from fastapi import WebSocket 

from src.domain.base import Entity

@dataclass(slots=True)
class Notification(Entity):
    websocket: WebSocket
    user_ip: str
    afisha_id: int
