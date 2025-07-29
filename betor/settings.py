from typing import Optional
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class FlareSolverrSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="flaresolverr_")

    base_url: Optional[str] = None

    @property
    def domain(self) -> Optional[str]:
        if not self.base_url:
            return None
        parsed = urlparse(self.base_url)
        return parsed.hostname


flaresolverr_settings = FlareSolverrSettings()
