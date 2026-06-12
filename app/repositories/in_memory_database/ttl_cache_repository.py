from cachetools import TTLCache
from datetime import timedelta
from abc import ABC, abstractmethod


opaque_access_cache = TTLCache(
    maxsize=100,
    ttl=timedelta(minutes=5).total_seconds(),
)
opaque_refresh_cache = TTLCache(
    maxsize=100,
    ttl=timedelta(days=15).total_seconds(),
)

class InMemoryTTLCacheBase(ABC):

    @abstractmethod
    def get(self, user_id: str):
        pass

    @abstractmethod
    def set(self, user_id: str, value):
        pass

    @abstractmethod
    def remove(self, user_id: str):
        pass




class OpaqueAccessInMemoryRepository(InMemoryTTLCacheBase):

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

class OpaqueRefreshInMemoryRepository(InMemoryTTLCacheBase):

    @property
    def opaque_refresh_cache(self) -> TTLCache:
        return opaque_refresh_cache

    def get(self, user_id: str):
        if user_id in self.opaque_refresh_cache:
            return self.opaque_refresh_cache[user_id]
        return None

    def set(self, user_id: str, value):
        try:
            self.opaque_refresh_cache[user_id] = value
            return True
        except Exception as e:
            return False

    def remove(self, user_id: str):
        if user_id in self.opaque_refresh_cache:
            self.opaque_refresh_cache.pop(user_id, None)
            return True
        return False