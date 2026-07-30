from cachetools import TTLCache
from datetime import timedelta
from asyncio import Lock


class ChatMessageCacheRepository:
    _ttl_cache: TTLCache | None = None
    _lock: Lock | None = None

    @classmethod
    def init_chat_messages_cache(cls):
        if cls._ttl_cache is None:
            cls._ttl_cache = TTLCache(
                maxsize=1000,
                ttl=timedelta(hours=10).total_seconds()
            )

    @classmethod
    def close_chat_messages_cache(cls):
        if cls._ttl_cache:
            cls._ttl_cache.clear()

    @classmethod
    def get_master_lock(cls) -> Lock:
        if cls._lock is None:
            cls._lock = Lock()
        return cls._lock


    @property
    def message_cache(self) -> TTLCache:
        return self._ttl_cache


    async def _add_value(self, user_id: str, value):
        async with self.get_master_lock():
            self.message_cache[user_id] = value

    async def _get_value(self, user_id: str):
        if user_id in self.message_cache:
            return self.message_cache[user_id]

        async with self.get_master_lock():
            new_value = []
            self.message_cache[user_id] = new_value
            return new_value

    async def append_messages(self, user_id: str, message):
        async with self.get_master_lock():
            current_messages = self.message_cache.setdefault(user_id, [])
            current_messages.append(message)






class ChatMessageCacheTestRepository:
    _ttl_cache: TTLCache | None = None
    _user_locks: TTLCache | None = None

    @classmethod
    def init_chat_messages_cache(cls):
        if cls._ttl_cache is None:
            cls._ttl_cache = TTLCache(
                maxsize=1000,
                ttl=timedelta(hours=10).total_seconds(),
            )

        if cls._user_locks is None:
            cls._user_locks = TTLCache(
                maxsize=1000,
                ttl=timedelta(hours=10).total_seconds(),
            )

    @classmethod
    def close_chat_messages_cache(cls):
        if cls._ttl_cache:
            cls._ttl_cache.clear()

        if cls._user_locks:
            cls._user_locks.clear()

    @property
    def message_cache(self) -> TTLCache:
        return self._ttl_cache

    @property
    def user_locks(self) -> TTLCache:
        return self._user_locks

    def get_user_lock(self, user_id: str) -> Lock:
        return self.user_locks.setdefault(user_id, Lock())

    async def get_messages(self, user_id: str):
        async with self.get_user_lock(user_id):
            return self.message_cache.setdefault(user_id, [])

    async def append_message(self, user_id: str, message):
        async with self.get_user_lock(user_id):
            messages = self.message_cache.setdefault(user_id, [])
            messages.append(message)