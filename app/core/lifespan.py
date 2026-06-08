from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo.asynchronous.database import AsyncDatabase
from pymongo import AsyncMongoClient
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from datetime import timedelta


from app.core.local_config import settings
from app.core.state import app_state


def get_jwt_redis_client():
    from redis import Redis
    return Redis(
            host='127.0.0.1',
            port=6379,
            db=0,
            max_connections=15,
            socket_timeout=5,
            retry_on_timeout=True
        )

def get_mongo_db_main_client() -> AsyncDatabase:
    _database_name = "database-name-test"
    _mongo_client = AsyncMongoClient(settings.mongo_db.get_secret_value())
    return _mongo_client[_database_name]




class MainMilvusClients:
    def __init__(self):
        self._embed_model = None
        self.api_key = settings.cohere_api_key
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.ttl = int(timedelta(days=7).total_seconds())

    @property
    def embed_model(self):
        if self._embed_model is None:
            self._embed_model = CohereEmbedding(
                model_name="embed-multilingual-v3.0",
                api_key=self.api_key.get_secret_value()
            )
        return self._embed_model

    @property
    def character_knowledge_index(self):
        _vector_store = MilvusVectorStore(
            collection_name="character_knowledge_base",
            **self._vector_config_params()
        )
        return self._indexing(vector_store=_vector_store)

    @property
    def message_store_index(self):
        _vector_store = MilvusVectorStore(
            collection_name="temporary_message_collection",
            collection_properties={"collection.ttl.seconds": self.ttl},
            **self._vector_config_params()
        )
        return self._indexing(vector_store=_vector_store)

    def _indexing(self, vector_store: MilvusVectorStore):
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self.embed_model,
            use_async=True
        )

    def _vector_config_params(self):
        return {
            "uri" : self.uri.get_secret_value(),
            "token" : self.token.get_secret_value(),
            "overwrite" : False,
            "dim" : 1024,
            "embedding_field" : "embeddings",
            "search_config" : {"nprobe": 60},
            "similarity_metric" :  "COSINE",
            "consistency_level" : "Session",
        }

def get_character_knowledge_index():
    milvus_object = MainMilvusClients()
    return milvus_object.character_knowledge_index

def get_message_store_index():
    milvus_object = MainMilvusClients()
    return milvus_object.message_store_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = app_state
    state.redis_jwt_client = get_jwt_redis_client()
    state.mongo_db_client = get_mongo_db_main_client()
    state.milvus_character_index = get_character_knowledge_index()
    state.milvus_message_index = get_message_store_index()

    try:
        yield

    finally:
        state.redis_jwt_client.close()
        state.milvus_message_index = None
        state.milvus_character_index = None
        state.mongo_db_client = None