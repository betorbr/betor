import redis

from betor.settings import database_redis_settings


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(database_redis_settings.url)
