from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from betor.entities import Episode
from betor.enums import ItemType
from betor.types import Languages


class ItemSchema(BaseModel):
    id: Optional[str]
    provider_slug: str
    provider_url: str
    imdb_id: Optional[str]
    tmdb_id: Optional[str]
    item_type: Optional[ItemType]
    magnet_uri: str
    magnet_xt: str
    magnet_dn: Optional[str]
    torrent_name: Optional[str]
    torrent_num_peers: Optional[int]
    torrent_num_seeds: Optional[int]
    torrent_files: Optional[List[str]]
    torrent_size: Optional[int]
    languages: Languages
    episodes: List[Episode]
    inserted_at: Optional[datetime]
    updated_at: Optional[datetime]
