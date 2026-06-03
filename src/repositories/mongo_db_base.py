from pymongo import AsyncMongoClient
from src.core.local_config import settings
from abc import ABC, abstractmethod



_CLIENT_MONGO_ASYNC = None
_DATABASE_NAME = "database-name-test"

def get_client() -> AsyncMongoClient:
    global _CLIENT_MONGO_ASYNC
    if _CLIENT_MONGO_ASYNC is None:
        _CLIENT_MONGO_ASYNC = AsyncMongoClient(settings.mongo_db.get_secret_value())
    return _CLIENT_MONGO_ASYNC


class AsyncMongoDbBaseClass(ABC):
    def __init__(self, collection_name: str):
        self.secret_host = settings.mongo_db
        self.collection_name = collection_name

    @property
    def client(self):
        global _CLIENT_MONGO_ASYNC
        if _CLIENT_MONGO_ASYNC is None:
            _CLIENT_MONGO_ASYNC = AsyncMongoClient(self.secret_host.get_secret_value())
        return _CLIENT_MONGO_ASYNC

    @property
    def database(self):
        return self.client[_DATABASE_NAME]

    @property
    def collection(self):
        return self.database[self.collection_name]