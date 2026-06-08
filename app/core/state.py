from redis import Redis
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from llama_index.vector_stores.milvus import MilvusVectorStore





class AppState:
    redis_jwt_client: Redis | None = None
    mongo_db_client: AsyncMongoClient | None = None
    milvus_character_vector: MilvusVectorStore | None = None
    milvus_message_vector: MilvusVectorStore | None = None

app_state = AppState()