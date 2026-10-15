# тут будет инициализация соединения с редис и создание глобального образца
from redis.asyncio import redis


class RedisHelper:
    def __init__(self, url:str, decode_responses: bool = True):
        self.pool = redis.ConnectionPool.from_url(url, max_connections = 10, decode_responses = decode_responses)
        self.connection = redis.Redis(connection_pool = pool)

redis_helper = RedisHelper(url = setting.redis_url)