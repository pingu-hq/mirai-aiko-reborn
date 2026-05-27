from typing import Any
from redis.asyncio import Redis
from asyncio.locks import Lock
from datetime import timedelta
import json



_REDIS_CLIENT = None
_REDIS_LOCK = None
_REDIS_EXPIRE_TIME = None

def redis_client() -> Redis:
    global _REDIS_CLIENT
    if _REDIS_CLIENT is None:
        _REDIS_CLIENT = Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True, socket_timeout=5)
    return _REDIS_CLIENT

def redis_lock() -> Lock:
    global _REDIS_LOCK
    if _REDIS_LOCK is None:
        _REDIS_LOCK = Lock()
    return _REDIS_LOCK

def redis_expire_time() -> timedelta:
    global _REDIS_EXPIRE_TIME
    if _REDIS_EXPIRE_TIME is None:
        _REDIS_EXPIRE_TIME = timedelta(days=1)
    return _REDIS_EXPIRE_TIME

class ClientState:
    def __init__(self, user_id: Any):
        self.redis = redis_client()
        self.lock = redis_lock()
        self.ttl = redis_expire_time()
        self.user_id = user_id

    async def _get(self):
        async with self.lock:
            serialized = await self.redis.get(self.user_id)
            if serialized:
                return json.loads(serialized)
            return None

    async def _add(self, data: Any):
        async with self.lock:
            serialized = json.dumps(data)
            return await self.redis.set(name=self.user_id, value=serialized)

    async def _add_with_ttl(self, data: Any):
        async with self.lock:
            serialized = json.dumps(data)
            return await self.redis.setex(name=self.user_id, value=serialized, time=self.ttl)


async def main():
    pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())