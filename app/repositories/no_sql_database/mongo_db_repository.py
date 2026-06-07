from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase, AsyncCollection
from app.core.local_config import settings



def get_db() -> AsyncDatabase:
    if not hasattr(get_db, "database"):
        _database_name = "database-name-test"
        _mongo_client = AsyncMongoClient(settings.mongo_db.get_secret_value())
        get_db.database = _mongo_client[_database_name]

    return get_db.database


class AsyncMongoDatabase:

    @property
    def db(self) -> AsyncDatabase:
        return get_db()

    def get_collection_by_name(self, collection_name: str) -> AsyncCollection:
        return self.db[collection_name]


class UsersCollectionRepository:
    def __init__(self):
        self.collection_name = "users"

    @property
    def users(self) -> AsyncCollection:
        _db = AsyncMongoDatabase()
        return _db.get_collection_by_name(self.collection_name)

class ConversationsCollectionRepository:
    def __init__(self):
        self.collection_name = "conversations"

    @property
    def conversations(self):
        _db = AsyncMongoDatabase()
        return _db.get_collection_by_name(self.collection_name)