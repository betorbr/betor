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
        env_file=".env", env_prefix="betor_celery_", extra="allow"
    )

    backend_url: str = "redis://localhost:6379/1"
    broker_url: str = "redis://localhost:6379/1"


class ScrapydSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="scrapyd_", extra="allow"
    )

    base_url: str = "http://localhost:6800"


class LibtorrentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="libtorrent_", extra="allow"
    )

    listen_interfaces: str = "0.0.0.0:6881"


class SearchJobMonitorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="search_job_monitor_", extra="allow"
    )

    ttl: int = 30 * 60


flaresolverr_settings = FlareSolverrSettings()
database_mongodb_settings = DatabaseMongoDBSettings()
database_redis_settings = DatabaseRedisSettings()
celery_settings = CelerySettings()
scrapyd_settings = ScrapydSettings()
libtorrent_settings = LibtorrentSettings()
search_job_monitor_settings = SearchJobMonitorSettings()
