from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase, AsyncCollection
from app.core.local_config import settings
from app.core.logger import app_logger


_mongo_db_client: AsyncMongoClient | None = None

def init_mongo_db_client():
    global _mongo_db_client
    app_logger.info("Starting mongo db client")
    _mongo_db_client = AsyncMongoClient(
        settings.mongo_db.get_secret_value()
    )

async def close_mongo_db_client():
    global _mongo_db_client
    app_logger.info("Closing mongo db client")
    if _mongo_db_client:
        await _mongo_db_client.close()
        _mongo_db_client = None


class AsyncMongoDatabase:
    _database_name = "database-name-test"

    @property
    def client(self) -> AsyncMongoClient:
        if _mongo_db_client is None:
            raise RuntimeError("MongoDB client not initialized")
        return _mongo_db_client


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