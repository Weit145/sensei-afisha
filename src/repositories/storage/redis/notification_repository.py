

from redis.asyncio import Redis

from src.repositories.storage.models.connectioninfo import (
    ConnectionInfo,
    NotificationType,
)
from src.repositories.storage.redis.db_helper import redis_helper


class RedisNotificationRepository:

    def __init__(self, redis) -> None:
        self.redis = redis_helper 

    async def save_notification(self, info: ConnectionInfo, ttl: int = 3600) -> None:
        """Сохраняет полную информацию о соединении в Redis."""
        key = f"conn:{info.connection_id}"
        await self.redis.hset(key, mapping={
            "connection_id": info.connection_id,
            "user_ip": info.user_ip,
            "server_id": str(info.server_id),
            "n_type": str(info.n_type.value),
            "afisha_id": str(info.afisha_id),
        })
        await self.redis.expire(key, ttl)

    async def load_connection(self, connection_id: str) -> ConnectionInfo | None:
        """Загружает ConnectionInfo из Redis по connection_id."""
        raw = await self.redis.hgetall(f"conn:{connection_id}")
        if not raw:
            return None
        return ConnectionInfo(
            connection_id=raw["connection_id"],
            user_ip=raw["user_ip"],
            server_id=int(raw["server_id"]),
            n_type=NotificationType(int(raw["n_type"])),
            afisha_id=int(raw["afisha_id"]),
        )

    async def drop_connection(self, connection_id: str) -> None:
        """Удаляет запись о соединении из Redis."""
        await self.redis.delete(f"conn:{connection_id}")

    async def connection_exists(self, connection_id: str) -> bool:
        """Проверяет, есть ли запись о соединении в Redis."""
        return bool(await self.redis.exists(f"conn:{connection_id}"))

    async def update_afisha_id(self, connection_id: str, afisha_id: int) -> None:
        """Обновляет только поле afisha_id."""
        await self.redis.hset(f"conn:{connection_id}", "afisha_id", str(afisha_id))

    async def update_n_type(self, connection_id: str, n_type: NotificationType) -> None:
        """Обновляет только поле n_type."""
        await self.redis.hset(f"conn:{connection_id}", "n_type", str(n_type.value))

    async def publish_to_server(self, server_id: int, payload: str) -> None:
        """Публикует сообщение в канал конкретного сервера."""
        await self.redis.publish(f"ws:server:{server_id}", payload)

redis_notification_repository = RedisNotificationRepository(redis_helper.connection)
