from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class FlareSolverrSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="flaresolverr_", extra="allow"
    )

    base_url: Optional[str] = None


class DatabaseMongoDBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="database_mongo_db_", extra="allow"
    )

    connection_uri: str = "mongodb://betor:betor@localhost:27017"
    betor_database: str = "betor"


class DatabaseRedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="database_redis_", extra="allow"
    )

    url: str = "redis://localhost:6379/0"


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="database_redis_", extra="allow"
    )

    backend_url: str = "redis://localhost:6379/1"
    broker_url: str = "redis://localhost:6379/1"


class ScrapydSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="scrapyd_", extra="allow"
    )

    base_url: str = "http://localhost:6800"


flaresolverr_settings = FlareSolverrSettings()
database_mongodb_settings = DatabaseMongoDBSettings()
database_redis_settings = DatabaseRedisSettings()
celery_settings = CelerySettings()
scrapyd_settings = ScrapydSettings()
