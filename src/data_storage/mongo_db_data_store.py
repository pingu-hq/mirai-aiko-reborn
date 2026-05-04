from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
import pymongo.errors
from src.core.local_config import settings
from src.core.security import SecurityAuth
import ulid



_users_collection: AsyncCollection | None = None

class MongoDbDataStore:
    def __init__(self):
        self.auth = SecurityAuth()

    @property
    def users(self) -> AsyncCollection:
        global _users_collection
        if _users_collection is None:
            _client = AsyncMongoClient(settings.mongo_db.get_secret_value())
            _db = _client["mirai-aiko-database"]
            _users_collection = _db["users"]
        return _users_collection


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

# import asyncio
# cleaning = MongoDbDataStore()
# asyncio.run(cleaning.reset_users_collection())