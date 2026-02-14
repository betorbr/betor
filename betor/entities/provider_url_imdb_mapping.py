from datetime import datetime
from typing import Optional, TypedDict


class ProviderURLIMDBMapping(TypedDict):
    id: Optional[str]
    inserted_at: Optional[datetime]
    updated_at: Optional[datetime]
    provider_url: str
    imdb_id: str
