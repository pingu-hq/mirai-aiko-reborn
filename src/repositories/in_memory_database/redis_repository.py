from datetime import timedelta
from redis import Redis


def jti_redis_client():
    if hasattr(jti_redis_client, "client"):
        jti_redis_client.client = Redis(
            host='127.0.0.1',
            port=6379,
            db=0,
            max_connections=15,
            socket_timeout=5,
            retry_on_timeout=True
        )
    return jti_redis_client.client

class JtiCacheRepository:
    def __init__(self):
        self.client = jti_redis_client()


    def get_value(self, name:str):
        return self.client.get(name=name)

    def set_value(self,name: str, time: int | timedelta, value):
        self.client.setex(name=name, time=time, value=value )

    def delete(self, name):
        self.client.delete(name)