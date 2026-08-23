from cachetools import TTLCache
from datetime import timedelta
from asyncio import Lock


class ChatMessageCacheRepository:
    _user_message_cache: TTLCache | None = None
    _user_locks: TTLCache | None = None
    # _lock: Lock | None = None

    @classmethod
    def init_chat_messages_cache(cls):
        if cls._user_message_cache is None:
            cls._user_message_cache = TTLCache(
                maxsize=1000,
                ttl=timedelta(hours=10).total_seconds()
            )
        if cls._user_locks is None:
            cls._user_locks = TTLCache(
                maxsize=1000,
                ttl=timedelta(hours=10).total_seconds()
            )

    @classmethod
    def close_chat_messages_cache(cls):
        if cls._user_message_cache:
            cls._user_message_cache.clear()

        if cls._user_locks:
            cls._user_locks.clear()

    @property
    def message_cache(self) -> TTLCache:
        return self._user_message_cache

    @property
    def user_locks(self) -> TTLCache:
        return self._user_locks

    def get_user_lock(self, user_id: str) -> Lock:
        return self.user_locks.setdefault(user_id, Lock())

    async def append_message(self, user_id: str, message):
        async with self.get_user_lock(user_id=user_id):
            current_messages = self.message_cache.setdefault(user_id, [])
            current_messages.append(message)

    async def get_messages(self, user_id: str):
        async with self.get_user_lock(user_id=user_id):
            return self.message_cache.setdefault(user_id, [])








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