from datetime import datetime
from typing import Optional, TypedDict

from .item_type import ItemType


class BaseItem(TypedDict):
    provider_slug: str
    provider_url: str
    imdb_id: Optional[str]
    tmdb_id: Optional[str]
    item_type: Optional[ItemType]


class Item(BaseItem):
    id: Optional[str]
    hash: Optional[int]
    inserted_at: Optional[datetime]
    updated_at: Optional[datetime]
    magnet_uri: str
    magnet_xt: str
    magnet_dn: Optional[str]
