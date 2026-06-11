from cachetools import TTLCache
from datetime import timedelta


opaque_access_cache = TTLCache(
    maxsize=100,
    ttl=timedelta(minutes=5).total_seconds(),
)
opaque_refresh_cache = TTLCache(
    maxsize=100,
    ttl=timedelta(days=15).total_seconds(),
)


class OpaqueAccessInMemoryRepository:

    @property
    def opaque_access_cache(self) -> TTLCache:
        return opaque_access_cache

    def get(self, user_id: str):
        if user_id in self.opaque_access_cache:
            return self.opaque_access_cache[user_id]
        return None

    def set(self, user_id: str, value):
        try:
            self.opaque_access_cache[user_id] = value
            return True
        except Exception as e:
            return False

    def remove(self, user_id: str):
        if user_id in self.opaque_access_cache:
            self.opaque_access_cache.pop(user_id, None)
            return True
        return False