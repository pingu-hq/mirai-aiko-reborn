from redis.asyncio import Redis, RedisError

from app.core.config import settings


class RedisCacheBaseRepository:
    _redis_asyncio_client: Redis | None = None

    @classmethod    
    def get_redis_client(cls) -> Redis:
        try:
            if cls._redis_asyncio_client:
                return cls._redis_asyncio_client
            raise RuntimeError("Redis client is not initialized")
        except RedisError as e:
            raise RuntimeError(f"Failed to get Redis client: {e}")

    @classmethod
    def init_redis_cache_repository(cls):
        if cls._redis_asyncio_client is None:
            cls._redis_asyncio_client: Redis = Redis.from_url(
                settings.redis_uri, decode_responses=True
            )

    @classmethod
    async def close_redis_cache_repository(cls):
        if cls._redis_asyncio_client:
            await cls._redis_asyncio_client.aclose()


