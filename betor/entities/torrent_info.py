from datetime import datetime
from typing import List, NotRequired, Optional, TypedDict


class TorrentInfo(TypedDict):
    torrent_name: Optional[str]
    torrent_files: Optional[List[str]]
    torrent_size: Optional[int]
    download_path: Optional[str]
    itorrent_uploaded_at: NotRequired[Optional[datetime]]
