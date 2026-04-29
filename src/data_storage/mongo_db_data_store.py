from pymongo import MongoClient
import pymongo.errors
from src.core.local_config import settings

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