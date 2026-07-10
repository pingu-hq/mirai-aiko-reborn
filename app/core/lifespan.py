from contextlib import asynccontextmanager
from fastapi import FastAPI
from asyncio import to_thread


from app.core.logger import app_logger
from app.repositories.in_memory_database.redis_repository import (
init_jwt_redis_client,
close_jwt_redis_client
)
from app.repositories.no_sql_database.mongo_db_repository import (
init_mongo_db_client,
close_mongo_db_client
)
from app.core.http_client import (
init_httpx_sync_client,
init_httpx_async_client,
close_httpx_sync_client,
close_httpx_async_client
)
from app.repositories.no_sql_database.milvus_vector_repository import (
init_cohere_embedding_model,
init_milvus_message_store,
init_milvus_character_knowledge,
close_milvus_message_store,
close_milvus_character_knowledge
)
from app.services.agents.sample_agent_service import (
init_azure_ai_project,
init_groq_client,
init_azure_client,
close_azure_openai_client,
close_azure_ai_project,
close_groq_client
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Fastapi Async context manager startup!")
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
        init_milvus_character_knowledge()
    except Exception as e:
        app_logger.error(f"Lifespan Milvus Character Error: {str(e)}")
        errors.append(f"Milvus character vector init failed: {str(e)}")

    try:
        init_milvus_message_store()
    except Exception as e:
        app_logger.error(f"Lifespan Milvus Message Error: {str(e)}")
        errors.append(f"Milvus message vector init failed: {str(e)}")

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
        init_azure_ai_project()
        init_azure_client()
    except Exception as e:
        app_logger.error(f"Lifespan Azure Client Error: {str(e)}")
        errors.append(f"Azure client init failed: {str(e)}")

    try:
        init_groq_client()
    except Exception as e:
        app_logger.error(f"Lifespan Groq Client Error: {str(e)}")
        errors.append(f"Groq client init failed: {str(e)}")





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

        await to_thread(close_milvus_character_knowledge)
        app_logger.info("Milvus character vector released!")

        await to_thread(close_milvus_message_store)
        app_logger.info("Milvus message vector released!")

        await to_thread(close_azure_openai_client)
        await to_thread(close_azure_ai_project)
        app_logger.info("Azure client released!")

        await close_groq_client()
        app_logger.info("Groq client released!")