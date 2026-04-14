import redis
from django.conf import settings
from urllib.parse import urlparse

_client = None

def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        url = urlparse(settings.CACHES["default"]["LOCATION"])
        _client = redis.Redis(
            host=url.hostname,
            port=url.port or 6379,
            password=url.password,
            db=0,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _client

def reset_redis_client():
    global _client
    _client = None