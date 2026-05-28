from typing import Any
from redis.asyncio import Redis
from asyncio.locks import Lock
from datetime import timedelta
from cachetools import TTLCache
import json


_REDIS_LOCK_HOLDER = None
_REDIS_CLIENT = None

def redis_client() -> Redis:
    global _REDIS_CLIENT
    if _REDIS_CLIENT is None:
        _REDIS_CLIENT = Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True, socket_timeout=5)
    return _REDIS_CLIENT

def global_lock_holder_object() -> TTLCache:
    global _REDIS_LOCK_HOLDER
    if _REDIS_LOCK_HOLDER is None:
        _REDIS_LOCK_HOLDER = TTLCache(maxsize=1000, ttl=timedelta(hours=2).total_seconds())
    return _REDIS_LOCK_HOLDER

def redis_lock_per_user(user_id: str) -> Lock:
    lock_holder = global_lock_holder_object()

    if user_id not in lock_holder:
        lock_holder.expire()
        lock_holder[user_id] = Lock()

    return lock_holder[user_id]






class RedisBaseClass:
    def __init__(self):
        self.redis = redis_client()

    async def _get(self, user_id: Any):
        lock = redis_lock_per_user(user_id)
        async with lock:
            serialized = await self.redis.get(user_id)
            if serialized:
                return json.loads(serialized)
            return None

    async def _add(self,user_id: Any, data: Any):
        lock = redis_lock_per_user(user_id)
        async with lock:
            serialized = json.dumps(data)
            return await self.redis.set(name=user_id, value=serialized)

    async def _add_with_ttl(self,user_id: Any, data: Any, time_to_live: int):
        lock = redis_lock_per_user(user_id)
        async with lock:
            serialized = json.dumps(data)
            return await self.redis.setex(name=user_id, value=serialized, time=time_to_live)









# async def main():
#     pass
#
# if __name__ == "__main__":
# import asyncio
#     asyncio.run(main())