from fastapi import HTTPException, status
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.mongo_client import AsyncMongoClient

from app.core.config import settings


class MongoBase:
    _database_name = "main-database"
    _client: AsyncMongoClient | None = None

    @classmethod
    def get_client(cls) -> AsyncMongoClient:
        if cls._client is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Mongo client not initialized")
        return cls._client

    @classmethod
    def init_mongo_client(cls):
        if cls._client is None:
            cls._client = AsyncMongoClient(settings.mongo_uri)

    @classmethod
    async def close_mongo_client(cls):
        if cls._client is not None:
            await cls._client.aclose()


class UsersRepository(MongoBase):
    _collection_name = "users"

    async def get_users_collection(self) -> AsyncCollection:
        mongo_client = self.get_client()
        user_collection = mongo_client[self._database_name][self._collection_name]
        await user_collection.create_index(keys="email", unique=True)
        return user_collection