# тут все операции сохранения, удаления, чтения сокетов 
from .db_helper import redis_helper
from src.repositories.storage.models import ConnectionInfo, NotificationType
from src.repositories.storage.map.notification import dict_to_model

class RedisNotificationRepository:
    def __init__(self, redis: redis_helper):
        self.redis = redis_helper

    async def save_notification(self, info: ConnectionInfo) -> None:
        key = f"conn:{info.user_ip}"
        await self.redis.hset(key, mapping = {
            "user_ip": info.user_ip, 
            "server_id": str(info.server_id),
            "n_type": str(info.n_type.value),
        })
        await self.redis.expire(key, 3600)
    
    async def load_connection(self, user_ip: str) ->ConnectionInfo| None:
        raw = await self.redis.hgetall(f"conn:{user_ip}")
        if not raw:
            return None
        return dict_to_model(user_ip, raw)
    
    async def drop_connection(self, user_ip: str) -> None:
        await self.redis.delete(f"conn:{user_ip}")
    
    async def connection_exists(self, user_ip: int) -> bool:
        return bool(await self.redis.exists(f"conn:{user_id}"))

