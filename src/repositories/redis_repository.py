from redis import Redis


def get_jwt_redis_client():
    if hasattr(get_jwt_redis_client, "client"):
        get_jwt_redis_client.client = Redis(
            host='127.0.0.1',
            port=6379,
            db=0,
            max_connections=15,
            socket_timeout=5,
            retry_on_timeout=True
        )
    return get_jwt_redis_client.client

class JtiCacheRepository:
    def __init__(self):
        self.client = get_jwt_redis_client()


    def get_value(self, name):
        return self.client.get(name=name)

    def set_value(self,name, time, value):
        self.client.setex(name=name, time=time, value=value )

    def delete(self, name):
        self.client.delete(name)