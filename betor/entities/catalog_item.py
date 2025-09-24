from datetime import datetime
from typing import List, Optional, TypedDict

from betor.enums import ItemType


class ProviderItemTorrent(TypedDict):
    magnet_uri: str
    languages: List[str]
    torrent_name: str
    torrent_size: int
    torrent_files: List[str]


class ProviderItem(TypedDict):
    slug: str
    url: str
    languages: List[str]
    torrents: List[ProviderItemTorrent]


class CatalogItem(TypedDict):
    item_type: ItemType
    imdb_id: Optional[str]
    tmdb_id: Optional[str]
    last_updated: datetime
    providers: List[ProviderItem]
