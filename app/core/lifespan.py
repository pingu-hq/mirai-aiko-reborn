from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo.asynchronous.database import AsyncDatabase
from pymongo import AsyncMongoClient


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





@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state.redis_jwt_client = get_jwt_redis_client()
    app_state.mongo_db_client = get_mongo_db_main_client()

    yield

    app_state.redis_jwt_client.close()