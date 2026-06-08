from redis import Redis
from pymongo.asynchronous.database import AsyncDatabase





class AppState:
    redis_jwt_client: Redis | None = None
    mongo_db_client: AsyncDatabase | None = None

app_state = AppState()