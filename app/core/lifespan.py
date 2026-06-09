from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from typing import Optional
from asyncio import to_thread
from datetime import timedelta
from redis import Redis
from httpx import AsyncClient, Client, Limits


from app.core.local_config import settings
from app.core.state import app_state


def get_jwt_redis_client():
    return Redis(
            host='127.0.0.1',
            port=6379,
            db=0,
            max_connections=15,
            socket_timeout=5,
            retry_on_timeout=True
        )

def get_mongo_db_main_client() -> AsyncMongoClient:
    return AsyncMongoClient(settings.mongo_db.get_secret_value())




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



class LifespanResources:

    @staticmethod
    def get_jwt_redis_client():
        return Redis(
            host='127.0.0.1',
            port=6379,
            db=0,
            max_connections=15,
            socket_timeout=5,
            retry_on_timeout=True
        )

    @staticmethod
    def get_mongo_db_main_client() -> AsyncMongoClient:
        return AsyncMongoClient(settings.mongo_db.get_secret_value())

    @staticmethod
    def get_milvus_character_knowledge():
        other_params = LifespanResources._vector_config_params()
        return MilvusVectorStore(
            collection_name="character_knowledge_base",
            **other_params
        )

    @staticmethod
    def get_milvus_message_store():
        _ttl = int(timedelta(days=7).total_seconds())
        other_params = LifespanResources._vector_config_params()
        return MilvusVectorStore(
            collection_name="temporary_message_collection",
            collection_properties={"collection.ttl.seconds": _ttl},
            **other_params
        )

    @staticmethod
    def get_httpx_client():
        _limits = LifespanResources._limits()
        return Client(
            timeout=30.0,
            limits=_limits
        )

    @staticmethod
    def get_httpx_async_client():
        _limits = LifespanResources._limits()
        return AsyncClient(
            timeout=30.0,
            limits=_limits
        )


    @staticmethod
    def get_cohere_embed_model(httpx_client: Optional[Client]=None, httpx_async_client: Optional[AsyncClient]=None):
        cohere_params = {
            "model_name" :"embed-multilingual-v3.0",
            "api_key" : settings.cohere_api_key.get_secret_value(),
        }
        if httpx_client:
            cohere_params["httpx_client"] = httpx_client

        if httpx_async_client:
            cohere_params["httpx_async_client"] = httpx_async_client

        return CohereEmbedding(**cohere_params)

    @staticmethod
    def get_azure_client():
        _secret_credentials = ClientSecretCredential(
            tenant_id=settings.tenant_id.get_secret_value(),
            client_id=settings.client_id.get_secret_value(),
            client_secret=settings.client_secret.get_secret_value(),
        )
        _azure_client = AIProjectClient(
            credential=_secret_credentials,
            endpoint=settings.ai_project_endpoint.get_secret_value()
        )
        return _azure_client.get_openai_client()

    @staticmethod
    def _vector_config_params():
        return {
            "uri" : settings.milvus_uri.get_secret_value(),
            "token" : settings.milvus_token.get_secret_value(),
            "overwrite" : False,
            "dim" : 1024,
            "embedding_field" : "embeddings",
            "search_config" : {"nprobe": 60},
            "similarity_metric" :  "COSINE",
            "consistency_level" : "Session",
        }

    @staticmethod
    def _limits():
        return Limits(
            max_keepalive_connections=10,
            max_connections=20
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan")
    state = app_state
    print("Import app_state")
    errors = []
    try:
        state.redis_jwt_client = LifespanResources.get_jwt_redis_client()
    except Exception as e:
        errors.append(f"Redis Jwt init failed: {str(e)}")
        state.redis_jwt_client = None

    try:
        state.mongo_db_client = LifespanResources.get_mongo_db_main_client()
    except Exception as e:
        errors.append(f"MongoDB async client init failed: {str(e)}")
        state.mongo_db_client = None

    try:
        state.milvus_character_vector = LifespanResources.get_milvus_character_knowledge()
    except Exception as e:
        errors.append(f"Milvus character vector init failed: {str(e)}")
        state.milvus_character_vector = None

    try:
        state.milvus_message_vector = LifespanResources.get_milvus_message_store()
    except Exception as e:
        errors.append(f"Milvus message vector init failed: {str(e)}")
        state.milvus_message_vector = None

    try:
        state.httpx_client = LifespanResources.get_httpx_client()
    except Exception as e:
        errors.append(f"Httpx client init failed: {str(e)}")
        state.httpx_client = None

    try:
        state.httpx_async_client = LifespanResources.get_httpx_async_client()
    except Exception as e:
        errors.append(f"Httpx async client init failed: {str(e)}")
        state.httpx_async_client = None


    try:
        state.cohere_embed_model = LifespanResources.get_cohere_embed_model(
            httpx_client=state.httpx_client,
            httpx_async_client=state.httpx_async_client
        )
    except Exception as e:
        errors.append(f"Cohere embed model init failed: {str(e)}")
        state.cohere_embed_model = None

    try:
        state.azure_client = LifespanResources.get_azure_client()
    except Exception as e:
        errors.append(f"Azure client init failed: {str(e)}")
        state.azure_client = None





    if errors:
        raise RuntimeError(f"Startup failed: {'; '.join(errors)}")

    print("app_state has no problem and theyre ready to go!")


    try:
        yield

    finally:
        if state.redis_jwt_client:
            await to_thread(state.redis_jwt_client.close)
            print("Redis client released!")

        if state.mongo_db_client:
            await state.mongo_db_client.close()
            print("MongoDB client released!")

        if state.milvus_character_vector:
            await to_thread(state.milvus_character_vector.client.close)
            print("Milvus character vector released!")

        if state.milvus_message_vector:
            await to_thread(state.milvus_message_vector.client.close)
            print("Milvus message vector released!")

        if state.httpx_client:
            await to_thread(state.httpx_client.close)
            print("Httpx client released!")

        if state.httpx_async_client:
            await state.httpx_async_client.aclose()
            print("Httpx async client released!")

        if state.azure_client:
            await to_thread(state.azure_client.close)
            print("Azure client released!")