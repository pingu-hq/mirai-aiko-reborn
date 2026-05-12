from redis import Redis
from typing import Any
from redis.asyncio import Redis as RedisAsync
from datetime import timedelta
from functools import lru_cache
import json



class JwtRedisStore:
    def __init__(self):
        self.expire_ttl = int(timedelta(days=15).total_seconds())
        self._redis = None

    @property
    def redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis(
                host='127.0.0.1',
                port=6379,
                db=0,
                max_connections=15,
                socket_timeout=5,
                retry_on_timeout=True
            )
        return self._redis

    def get_(self, _key: Any):

        _name = f"jti=={_key}"
        raw_data = self.redis.get(name=_name)
        if not raw_data:
            return None

        return json.loads(raw_data)

    def set_(self, _key: Any, value: Any, ttl: int = 0):
        _name = f"jti=={_key}"
        serialized = json.dumps(value)
        if ttl == 0:
            ttl = self.expire_ttl
        self.redis.set(name=_name, value=serialized, ex=ttl)

    def delete_(self, _key: str):
        _name = f"jti=={_key}"
        self.redis.delete(_name)

@lru_cache()
def jwt_redis():
    return JwtRedisStore()

class MemoryStore:
    def __init__(self):
        self._redis = None

    @property
    def redis(self) -> RedisAsync:
        if self._redis is None:
            self._redis = RedisAsync(host='127.0.0.1', port=6379, db=0)
        return self._redis

    async def post(self, _id: str | Any, value: Any, ttl: int = 3600):
        serialized = json.dumps(value)
        return await self.redis.set(_id, serialized, ex=ttl)

    async def get(self, _id: str | Any) -> Any:
        serialized = await self.redis.get(_id)
        if serialized:
            return json.loads(serialized)
        return None

# memory = MemoryStore()