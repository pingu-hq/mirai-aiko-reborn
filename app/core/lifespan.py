from contextlib import asynccontextmanager
from fastapi import FastAPI
from asyncio import to_thread


from app.core.logger import app_logger
from app.repositories.in_memory_database.redis_repository import (
init_jwt_redis_client,
close_jwt_redis_client,
init_redis_client_async,
close_redis_client_async
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
from app.services.data.memory_service import (
init_memory_client,
close_memory_client
)
from app.core.agents.agent_loader import init_yaml_loader
from app.core.agents.crew_factory import (
init_cache_and_crew_llms,
close_cache_and_crew_llms
)


async def safe_closure(name: str, close_func, is_sync: bool = True):
    try:
        if is_sync:
            await to_thread(close_func)
        else:
            await close_func()
        app_logger.info(f"{name} is released successfully")
    except Exception as e:
        app_logger.error(f"Failed to release {name}: Error details: {str(e)}")

def safe_init(name: str, init_func, strict: bool = True):
    try:
        init_func()
        app_logger.info(f"{name} is initialized successfully")
    except Exception as e:
        app_logger.error(f"Failed to run {name}: {str(e)}")
        if strict:
            raise RuntimeError(f"Critical startup failure in {init_func.__name__}") from e
        else:
            app_logger.warning(f">>{name}<< failed to initialize but operation will continue. Beware of side effects.")



@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Fastapi Async context manager startup!")
    try:
        safe_init("Redis Jwt Client", init_jwt_redis_client)
        safe_init("Redis Async Client", init_redis_client_async)
        safe_init("MongoDb Client", init_mongo_db_client)
        safe_init("Milvus client character knowledge", init_milvus_character_knowledge)
        safe_init("Milvus client message store", init_milvus_message_store)
        safe_init("Httpx sync client", init_httpx_sync_client)
        safe_init("Httpx async client", init_httpx_async_client)
        safe_init("Cohere embedding model", init_cohere_embedding_model)
        safe_init("Azure AI Project", init_azure_ai_project)
        safe_init("Azure Client", init_azure_client)
        safe_init("Groq Client", init_groq_client)
        safe_init("Mem0 Client", init_memory_client)
        safe_init("Yaml crewai config", init_yaml_loader)
        safe_init("Crewai LLM and Cache", init_cache_and_crew_llms)
        yield

    finally:
        await safe_closure("Redis Jwt Client", close_jwt_redis_client, is_sync=True)
        await safe_closure("Redis Async Client", close_redis_client_async, is_sync=False)
        await safe_closure("MongoDb Client", close_mongo_db_client, is_sync=False)
        await safe_closure("Milvus client character knowledge", close_milvus_character_knowledge, is_sync=True)
        await safe_closure("Milvus client message store", close_milvus_message_store, is_sync=True)
        await safe_closure("Httpx sync client", close_httpx_sync_client, is_sync=True)
        await safe_closure("Httpx async client", close_httpx_async_client, is_sync=False)
        await safe_closure("Azure AI Project", close_azure_ai_project, is_sync=True)
        await safe_closure("Azure Client", close_azure_openai_client, is_sync=True)
        await safe_closure("Groq Client", close_groq_client, is_sync=False)
        await safe_closure("Mem0 Client", close_memory_client, is_sync=True)
        await safe_closure("Crewai LLM and Cache", close_cache_and_crew_llms, is_sync=True)