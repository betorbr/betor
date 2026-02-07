from typing import List, Optional, TypedDict


class TorrentInfo(TypedDict):
    torrent_name: Optional[str]
    torrent_files: Optional[List[str]]
    torrent_size: Optional[int]
