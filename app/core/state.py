from redis import Redis
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from llama_index.core import VectorStoreIndex





class AppState:
    redis_jwt_client: Redis | None = None
    mongo_db_client: AsyncMongoClient | None = None
    milvus_character_index: VectorStoreIndex | None = None
    milvus_message_index: VectorStoreIndex | None = None

app_state = AppState()