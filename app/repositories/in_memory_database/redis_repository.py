import json
from datetime import timedelta
from typing import Any

from redis import Redis, RedisError
from redis.asyncio.client import Redis as RedisAsync
from app.core.exceptions import check_property_runtime


_redis_client: Redis | None = None

def init_jwt_redis_client():
    global _redis_client
    _redis_client = Redis(
        host='127.0.0.1',
        port=6379,
        db=0,
        max_connections=15,
        socket_timeout=5,
    )


def close_jwt_redis_client():
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None



class JtiCacheRepository:

    @property
    def client(self) -> Redis:
        return check_property_runtime("Redis jwt client", _redis_client)



    def get_value(self, name:str):
        return self.client.get(name=name)

    def set_value(self,name: str, time: int | timedelta, value):
        self.client.setex(name=name, time=time, value=value )

    def delete(self, name):
        self.client.delete(name)



_redis_client_async: RedisAsync | None = None

def init_redis_client_async():
    global _redis_client_async
    if _redis_client_async is None:
        _redis_client_async = RedisAsync(
            host='127.0.0.1',
            port=6379,
            db=0,
            decode_responses=True
        )

async def close_redis_client_async():
    global _redis_client_async
    if _redis_client_async:
        await _redis_client_async.aclose()

class RedisAsyncRepository:

    @property
    def redis_client(self) -> RedisAsync:
        return _redis_client_async


    async def add_value(self, input_key: str, input_value: str | dict[str, Any] | bytes, exp: timedelta):
        try:
            if isinstance(input_value, dict):
                input_value = json.dumps(input_value)
            await self.redis_client.set(
                name=input_key,
                value=input_value,
                ex=exp
            )
            return True
        except RedisError as e:
            raise RedisError(e)
        except Exception as e:
            raise e

    async def get_value(self, input_key: str):
        try:
            raw_output_string = await self.redis_client.get(name=input_key)

            if raw_output_string is not None:
                return json.loads(raw_output_string)

            return None
        except json.JSONDecodeError as e:
            raise RedisError(e)
        except Exception as e:
            raise e

    async def delete_value(self, input_key):
        if input_key is not None:
            await self.redis_client.delete(input_key)
            return True
        return False
