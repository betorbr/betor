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


flaresolverr_settings = FlareSolverrSettings()
database_mongodb_settings = DatabaseMongoDBSettings()
