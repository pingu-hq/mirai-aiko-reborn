from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase, AsyncCollection
from app.core.state import app_state



# def get_db() -> AsyncDatabase:
#     if not hasattr(get_db, "database"):
#         _database_name = "database-name-test"
#         _mongo_client = AsyncMongoClient(settings.mongo_db.get_secret_value())
#         get_db.database = _mongo_client[_database_name]
#
#     return get_db.database


class AsyncMongoDatabase:
    _database_name = "database-name-test"

    @property
    def client(self) -> AsyncMongoClient:
        if not app_state.mongo_db_client:
            raise RuntimeError("MongoDB client not initialized")
        return app_state.mongo_db_client


    @property
    def database(self) -> AsyncDatabase:
        return self.client[self._database_name]

    def get_collection_by_name(self, collection_name: str) -> AsyncCollection:
        return self.database[collection_name]


class UsersCollectionRepository:
    def __init__(self):
        self.collection_name = "users"
        self.db = AsyncMongoDatabase()

    @property
    def users(self) -> AsyncCollection:
        return self.db.get_collection_by_name(self.collection_name)

class ConversationsCollectionRepository:
    def __init__(self):
        self.collection_name = "conversations"
        self.db = AsyncMongoDatabase()

    @property
    def conversations(self):
        return self.db.get_collection_by_name(self.collection_name)