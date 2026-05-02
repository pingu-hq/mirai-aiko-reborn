from redis import Redis
from typing import Any
from redis.asyncio import Redis as RedisAsync
import json



r = Redis(host='127.0.0.1', port=6379, db=0)

def get_redis_by_id(_id: str):
    raw_data = r.get(_id)
    if raw_data:
        return json.loads(raw_data)
    return None

def set_redis(_id: str, value: Any, ttl: int = 3600):
    serialized = json.dumps(value)
    return r.set(_id, serialized, ex=ttl)

class MemoryStore:
    def __init__(self):
        self._redis: RedisAsync | None = None

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

memory = MemoryStore()