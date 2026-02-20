from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, computed_field

from betor.entities import Episode
from betor.enums import ItemType
from betor.settings import store_torrent_file_settings
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
    download_path: Optional[str]
    languages: Languages
    episodes: List[Episode]
    seasons: List[int]
    inserted_at: Optional[datetime]
    updated_at: Optional[datetime]

    @computed_field
    def download_url(self) -> Optional[str]:
        if store_torrent_file_settings.public_download_base_url and self.download_path:
            return f"{store_torrent_file_settings.public_download_base_url}/{self.download_path}"
        return None
