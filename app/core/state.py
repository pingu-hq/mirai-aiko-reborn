from redis import Redis
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from openai import OpenAI
from httpx import AsyncClient, Client





class AppState:
    redis_jwt_client: Redis | None = None
    mongo_db_client: AsyncMongoClient | None = None
    milvus_character_vector: MilvusVectorStore | None = None
    milvus_message_vector: MilvusVectorStore | None = None
    azure_client: OpenAI | None = None
    cohere_embed_model: CohereEmbedding | None = None
    httpx_client: Client | None = None
    httpx_async_client: AsyncClient | None = None

app_state = AppState()