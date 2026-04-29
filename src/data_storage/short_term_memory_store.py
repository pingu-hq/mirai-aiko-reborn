from redis import Redis
from typing import Any
import redis.asyncio as redis_async
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