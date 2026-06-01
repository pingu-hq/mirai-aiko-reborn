from pymongo import AsyncMongoClient
from src.core.local_config import settings



_CLIENT_MONGO_ASYNC = None

def get_client() -> AsyncMongoClient:
    global _CLIENT_MONGO_ASYNC
    if _CLIENT_MONGO_ASYNC is None:
        _CLIENT_MONGO_ASYNC = AsyncMongoClient(settings.mongo_db.get_secret_value())
    return _CLIENT_MONGO_ASYNC

def get_mirai_aiko_db():
    _client = get_client()
    return _client["mirai-aiko-database"]

def get_collection_by_name(name: str):
    _db = get_mirai_aiko_db()
    return _db[name]