from datetime import timedelta
from redis import Redis
from app.core.logger import app_logger


_redis_client: Redis | None = None

def init_jwt_redis_client():
    global _redis_client
    app_logger.info("Starting redis client!")
    _redis_client = Redis(
        host='127.0.0.1',
        port=6379,
        db=0,
        max_connections=15,
        socket_timeout=5,
        retry_on_timeout=True
    )


def close_jwt_redis_client():
    app_logger.info("Closing redis client!")
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None



class JtiCacheRepository:

    @property
    def client(self) -> Redis:
        if _redis_client is None:
            raise RuntimeError("Redis not initialized")
        return _redis_client



    def get_value(self, name:str):
        return self.client.get(name=name)

    def set_value(self,name: str, time: int | timedelta, value):
        self.client.setex(name=name, time=time, value=value )

    def delete(self, name):
        self.client.delete(name)