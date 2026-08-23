from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase, AsyncCollection
from app.core.local_config import settings
from app.core.exceptions import check_property_runtime


_mongo_db_client: AsyncMongoClient | None = None

def init_mongo_db_client():
    global _mongo_db_client
    _mongo_db_client = AsyncMongoClient(
        settings.mongo_db.get_secret_value()
    )

async def close_mongo_db_client():
    global _mongo_db_client
    if _mongo_db_client:
        await _mongo_db_client.close()
        _mongo_db_client = None


class AsyncMongoDatabase:
    _database_name = "database-name-test"

    @property
    def client(self) -> AsyncMongoClient:
        return check_property_runtime("MongoDb Client", _mongo_db_client)


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