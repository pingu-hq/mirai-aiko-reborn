from pymongo import MongoClient, AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
import pymongo.errors
from src.core.local_config import settings
from src.core.security import SecurityAuth

# 1. Connect once
client = MongoClient(settings.mongo_db.get_secret_value())
db = client["mirai-aiko-database"]
coll_users = db["users"]


def init_db():
    try:
        coll_users.create_index("email", unique=True)
        print("✅ Unique index on 'email' is ready.")
    except pymongo.errors.OperationFailure as e:
        print(f"ℹ️ Index status: {e}")

def create_user(email: str, password: str):
    init_db()  # Safe to call repeatedly; only acts if missing
    try:
        result = coll_users.insert_one({
            "email": email,
            "password": password
        })
        return {"success": True, "user_id": str(result.inserted_id)}

    except pymongo.errors.DuplicateKeyError:
        return {"success": False, "error": "Email already registered"}

    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_by_email(email: str):
    init_db()
    return coll_users.find_one({"email": email})


# # === Test Flow ===
# res = create_user("test_email", "1234")
# print("Create attempt 1:", res)
#
# res2 = create_user("test_email", "5678")  # Same email
# print("Create attempt 2:", res2)
#
# print("Fetch user:", get_user_by_email("test_email"))
#
# # db.drop_collection("users")
# # coll_users.drop()

# 1. Connect once
_users_collection: AsyncCollection | None = None

class MongoDbDataStore:
    def __init__(self):
        self.auth = SecurityAuth()

    def init_db(self):
        try:
            self.users.create_index("email", unique=True)
        except pymongo.errors.OperationFailure as e:
            print(f"ℹ️ Index status: {e}")

    @property
    def users(self) -> AsyncCollection:
        global _users_collection
        if _users_collection is None:
            _client = AsyncMongoClient(settings.mongo_db.get_secret_value())
            _db = _client["mirai-aiko-database"]
            _users_collection = _db["users"]
        return _users_collection


    async def create_user(self, email: str, password: str, name: str):
        self.init_db()
        hashed_password = await self.auth.get_hash_password(password)
        to_user_db = {
            "email": email,
            "password": hashed_password,
            "name": name
        }
        _insert = await self.users.insert_one(to_user_db)
        return _insert.inserted_id

    async def get_user_by_email(self, email: str):
        self.init_db()
        return await self.users.find_one({"email": email})
