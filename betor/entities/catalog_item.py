from datetime import datetime
from typing import List, Optional, TypedDict

from betor.enums import ItemType


class ProviderPage(TypedDict):
    slug: str
    url: str
    languages: List[str]
    torrent_names: List[str]


class CatalogItem(TypedDict):
    item_type: ItemType
    imdb_id: Optional[str]
    tmdb_id: Optional[str]
    last_updated: datetime
    provider_pages: List[ProviderPage]
