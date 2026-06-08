from redis import Redis
from pymongo.asynchronous.database import AsyncDatabase
from llama_index.core import VectorStoreIndex





class AppState:
    redis_jwt_client: Redis | None = None
    mongo_db_client: AsyncDatabase | None = None
    milvus_character_index: VectorStoreIndex | None = None
    milvus_message_index: VectorStoreIndex | None = None

app_state = AppState()