from contextlib import asynccontextmanager
from fastapi import FastAPI
from llama_index.vector_stores.milvus import MilvusVectorStore
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from asyncio import to_thread
from datetime import timedelta
from groq import AsyncGroq


from app.core.local_config import settings
from app.core.state import app_state
from app.core.logger import app_logger
from app.repositories.in_memory_database.redis_repository import init_jwt_redis_client, close_jwt_redis_client
from app.repositories.no_sql_database.mongo_db_repository import init_mongo_db_client, close_mongo_db_client
from app.core.http_client import (
    init_httpx_sync_client,
    init_httpx_async_client,
    close_httpx_sync_client,
    close_httpx_async_client
)
from app.repositories.no_sql_database.milvus_vector_repository import init_cohere_embedding_model



class LifespanResources:

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
    def get_milvus_character_knowledge():
        app_logger.info("Starting milvus character knowledge!")
        other_params = LifespanResources._vector_config_params()
        return MilvusVectorStore(
            collection_name="character_knowledge_base",
            **other_params
        )

    @staticmethod
    def get_milvus_message_store():
        app_logger.info("Starting milvus message store!")
        _ttl = int(timedelta(days=7).total_seconds())
        other_params = LifespanResources._vector_config_params()
        return MilvusVectorStore(
            collection_name="temporary_message_collection",
            collection_properties={"collection.ttl.seconds": _ttl},
            **other_params
        )


    @staticmethod
    def get_azure_client():
        app_logger.info("Starting azure client!")
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
    def get_groq_client():
        app_logger.info("Starting groq client!")
        return AsyncGroq(api_key=settings.groq_api_key.get_secret_value())

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Fastapi Async context manager startup!")
    state = app_state
    errors = []
    try:
        init_jwt_redis_client()
    except Exception as e:
        app_logger.error(f"Lifespan Redis Error: {str(e)}")
        errors.append(f"Redis Jwt init failed: {str(e)}")

    try:
        init_mongo_db_client()
    except Exception as e:
        app_logger.error(f"Lifespan MongoDb Error: {str(e)}")
        errors.append(f"MongoDB async client init failed: {str(e)}")

    try:
        state.milvus_character_vector = LifespanResources.get_milvus_character_knowledge()
    except Exception as e:
        app_logger.error(f"Lifespan Milvus Character Error: {str(e)}")
        errors.append(f"Milvus character vector init failed: {str(e)}")
        state.milvus_character_vector = None

    try:
        state.milvus_message_vector = LifespanResources.get_milvus_message_store()
    except Exception as e:
        app_logger.error(f"Lifespan Milvus Message Error: {str(e)}")
        errors.append(f"Milvus message vector init failed: {str(e)}")
        state.milvus_message_vector = None

    try:
        init_httpx_sync_client()
    except Exception as e:
        app_logger.error(f"Lifespan Httpx Client Error: {str(e)}")
        errors.append(f"Httpx client init failed: {str(e)}")

    try:
        init_httpx_async_client()
    except Exception as e:
        app_logger.error(f"Lifespan Httpx Async Client Error: {str(e)}")
        errors.append(f"Httpx async client init failed: {str(e)}")


    try:
        init_cohere_embedding_model()
    except Exception as e:
        app_logger.error(f"Lifespan Cohere Embed Error: {str(e)}")
        errors.append(f"Cohere embed model init failed: {str(e)}")

    try:
        state.azure_client = LifespanResources.get_azure_client()
    except Exception as e:
        app_logger.error(f"Lifespan Azure Client Error: {str(e)}")
        errors.append(f"Azure client init failed: {str(e)}")
        state.azure_client = None

    try:
        state.groq_client = LifespanResources.get_groq_client()
    except Exception as e:
        app_logger.error(f"Lifespan Groq Client Error: {str(e)}")
        errors.append(f"Groq client init failed: {str(e)}")
        state.groq_client = None





    if errors:
        collective_error = f"Startup failed: {'; '.join(errors)}"
        app_logger.error(f"Collective Error -> {collective_error}")
        raise RuntimeError(collective_error)


    try:
        yield

    finally:
        await to_thread(close_jwt_redis_client)
        app_logger.info("Redis client released!")

        await close_mongo_db_client()
        app_logger.info("MongoDB client released!")

        await to_thread(close_httpx_sync_client)
        app_logger.info("Httpx client released!")

        await close_httpx_async_client()
        app_logger.info("Httpx async client released!")

        if state.milvus_character_vector:
            await to_thread(state.milvus_character_vector.client.close)
            app_logger.info("Milvus character vector released!")

        if state.milvus_message_vector:
            await to_thread(state.milvus_message_vector.client.close)
            app_logger.info("Milvus message vector released!")

        if state.azure_client:
            await to_thread(state.azure_client.close)
            app_logger.info("Azure client released!")

        if state.groq_client:
            await state.groq_client.close()
            app_logger.info("Groq client released!")