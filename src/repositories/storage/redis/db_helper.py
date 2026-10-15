# тут будет инициализация соединения с редис и создание глобального образца
from redis.asyncio import redis

from src.core.config import settings


class RedisHelper:
    def __init__(self, url:str, decode_responses: bool = True):
        self.pool = redis.ConnectionPool.from_url(url, max_connections = 10, decode_responses = decode_responses)
        self.connection = redis.Redis(connection_pool = self.pool)

redis_helper = RedisHelper(url=settings.redis_url)
