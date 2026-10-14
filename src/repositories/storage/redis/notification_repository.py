from redis.asyncio import Redis

from src.repositories.storage.models.connectioninfo import (
    ConnectionInfo,
    NotificationType,
)

from src.repositories.storage.redis.db_helper import redis_helper


class RedisNotificationRepository:
    """
    Все операции с Redis, связанные с соединениями пользователей.
    Ключ: conn:{user_ip}
    """

    def __init__(self, redis: redis_helper) -> None:
        self.redis = redis

    async def save_notification(self, info: ConnectionInfo, ttl: int = 3600) -> None:
        """
        Сохраняет полную информацию о соединении в Redis.
        Ключ — conn:{user_ip}. TTL по умолчанию 1 час.
        """
        key = f"conn:{info.user_ip}"
        await self.redis.hset(key, mapping={
            "user_ip": info.user_ip,
            "server_id": str(info.server_id),
            "n_type": str(info.n_type.value),
            "afisha_id": str(info.afisha_id),
        })
        await self.redis.expire(key, ttl)

    async def load_connection(self, user_ip: str) -> ConnectionInfo | None:
        """
        Загружает ConnectionInfo из Redis по user_ip.
        Возвращает None, если записи нет.
        """
        raw = await self.redis.hgetall(f"conn:{user_ip}")
        if not raw:
            return None
        return ConnectionInfo(
            user_ip=raw["user_ip"],
            server_id=int(raw["server_id"]),
            n_type=NotificationType(int(raw["n_type"])),
            afisha_id=int(raw["afisha_id"]),
        )

    async def drop_connection(self, user_ip: str) -> None:
        """Удаляет запись о соединении из Redis."""
        await self.redis.delete(f"conn:{user_ip}")

    async def connection_exists(self, user_ip: str) -> bool:
        """Проверяет, есть ли запись о соединении в Redis."""
        return bool(await self.redis.exists(f"conn:{user_ip}"))


    async def update_afisha_id(self, user_ip: str, afisha_id: int) -> None:
        """Обновляет только поле afisha_id. Быстрее, чем save_notification целиком."""
        await self.redis.hset(f"conn:{user_ip}", "afisha_id", str(afisha_id))

    async def update_n_type(self, user_ip: str, n_type: NotificationType) -> None:
        """Обновляет только поле n_type (текущий экран)."""
        await self.redis.hset(f"conn:{user_ip}", "n_type", str(n_type.value))

    async def publish_to_server(self, server_id: int, payload: str) -> None:
        """Публикует сообщение в канал конкретного сервера."""
        await self.redis.publish(f"ws:server:{server_id}", payload)

redis_notification_repository = RedisNotificationRepository()