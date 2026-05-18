from enum import StrEnum
from redis import Redis
from typing import Any
from redis.asyncio import Redis as RedisAsync
from datetime import timedelta
from functools import lru_cache
from asyncio import Lock
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


@lru_cache()
def memory():
    return MemoryStore()










class Role(StrEnum):
    USER = "user"
    ASST = "assistant"


@lru_cache()
def redis_client_for_messages() -> RedisAsync:
    return RedisAsync(host='127.0.0.1', port=6379, db=0, decode_responses=True, socket_timeout=5)

@lru_cache(maxsize=1000)
def get_user_locks(user_id: str):
    return Lock()

class MessageStore:
    def __init__(self, user_id):
        self.redis_client = redis_client_for_messages()
        self._user_id = str(user_id)

    @property
    def user_id(self):
        return f"message_store_{self._user_id}"

    @staticmethod
    def list_to_str(data) -> str:
        return json.dumps(data)

    @staticmethod
    def str_to_list(data: str):
        return json.loads(data)

    @staticmethod
    def chat_history_fusion(role: str, content: str | list[dict[str, Any]], chat_history: list[dict]) -> list:
        if isinstance(content, str):
            new_message: list = [{"role": role, "content": content}]
        else:
            new_message = content

        chat_history.extend(new_message)
        return chat_history

    async def _add_messages_to_redis(self, value: str):
        lock = get_user_locks(user_id=self.user_id)
        async with lock:
            await self.redis_client.setex(
                name=self.user_id,
                value=value,
                time=timedelta(hours=20)
            )
            return self

    async def _get_chat_history(self):
        lock = get_user_locks(self.user_id)
        async with lock:
            raw = await self.redis_client.get(self.user_id)
            if raw == "[]" or raw is None:
                return []

            return self.str_to_list(raw)

    async def add_user_message(self, input_message):
        get_history = await self._get_chat_history()
        new_history = self.chat_history_fusion(role=Role.USER, content=input_message, chat_history=get_history)
        value = self.list_to_str(new_history)
        await self._add_messages_to_redis(value=value)
        return new_history

    async def add_assistant_message(self, input_message):
        get_history = await self._get_chat_history()
        new_history = self.chat_history_fusion(role=Role.ASST, content=input_message, chat_history=get_history)
        value = self.list_to_str(new_history)
        await self._add_messages_to_redis(value=value)
        return new_history

    async def get_chat_history(self):
        return await self._get_chat_history()