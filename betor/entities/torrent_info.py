from typing import List, Optional, TypedDict


class TorrentInfo(TypedDict):
    torrent_name: Optional[str]
    torrent_num_peers: Optional[int]
    torrent_num_seeds: Optional[int]
    torrent_files: Optional[List[str]]
    torrent_size: Optional[int]
