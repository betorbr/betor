from typing import Optional, TypedDict


class TorrentTrackersInfo(TypedDict):
    torrent_num_peers: Optional[int]
    torrent_num_seeds: Optional[int]
