from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
import pymongo.errors
from src.core.local_config import settings
from src.core.security import SecurityAuth
import ulid




_CLIENT_MONGO_ASYNC = None

def get_client() -> AsyncMongoClient:
    global _CLIENT_MONGO_ASYNC
    if _CLIENT_MONGO_ASYNC is None:
        _CLIENT_MONGO_ASYNC = AsyncMongoClient(settings.mongo_db.get_secret_value())
    return _CLIENT_MONGO_ASYNC

def get_db():
    _client = get_client()
    return _client["mirai-aiko-database"]

def get_collection_by_name(name: str):
    _db = get_db()
    return _db[name]


def users_collection():
    return get_collection_by_name("users")

def conversation_collection():
    return get_collection_by_name("conversations")





class MongoDbDataStore:
    def __init__(self):
        self.auth = SecurityAuth()

    @property
    def users(self) -> AsyncCollection:
        return users_collection()

    @property
    def conversations(self) -> AsyncCollection:
        return conversation_collection()


    async def create_user(self, email: str, password: str, name: str):
        try:
            hashed_password = await self.auth.get_hash_password(password)
            external_id = str(ulid.new())
            to_user_db = {
                "email": email,
                "password": hashed_password,
                "name": name,
                "external_id": external_id
            }
            _insert = await self.users.insert_one(to_user_db)
            return True
        except pymongo.errors.DuplicateKeyError:
            return False
        except Exception as ex:
            raise ex


    async def get_id_and_password(self, email: str):
        user_info = await self.users.find_one({"email": email})
        if not user_info:
            return "", ""

        current_external_id = user_info.get("external_id")
        current_password = user_info.get("password")

        return current_external_id, current_password

    async def reset_users_collection(self):
        """Purges the users collection for development resets."""
        await self.users.drop()

        # Rebuild unique indexes immediately after the collection is cleared
        await self.users.create_index("email", unique=True)
        await self.users.create_index("external_id", unique=True)

    async def get_conversation_info(self, user_id: str):
        conversation_info = await self.conversations.find_one(
            {"external_id": user_id},
            sort=[("_id", -1)]
        )
        if not conversation_info or conversation_info == "":
            return None
        return conversation_info

# import asyncio
# cleaning = MongoDbDataStore()
# asyncio.run(cleaning.reset_users_collection())