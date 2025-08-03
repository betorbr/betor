from datetime import datetime
from typing import List, Optional, TypedDict


class RawItem(TypedDict):
    id: Optional[str]
    hash: Optional[int]
    inserted_at: Optional[datetime]
    updated_at: Optional[datetime]
    provider_slug: str
    provider_url: str
    imdb_id: Optional[str]
    magnet_links: List[str]
    languages: List[str]
    qualitys: List[str]
    title: Optional[str]
    translated_title: Optional[str]
    raw_title: Optional[str]
    year: Optional[int]
