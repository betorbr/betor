from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProviderURLIMDBMappingSchema(BaseModel):
    id: Optional[str]
    inserted_at: Optional[datetime]
    updated_at: Optional[datetime]
    provider_url: str
    imdb_id: str
