from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class FlareSolverrSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="flaresolverr_")

    base_url: Optional[str] = None


flaresolverr_settings = FlareSolverrSettings()
