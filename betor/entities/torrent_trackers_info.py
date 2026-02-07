from typing import List, Optional, TypedDict


class TorrentTrackerInfo(TypedDict):
    tracker_url: Optional[str]
    num_peers: Optional[int]
    num_seeds: Optional[int]
    num_complete: Optional[int]


class TorrentTrackersInfo(TypedDict):
    torrent_num_peers: Optional[int]
    torrent_num_seeds: Optional[int]
    torrent_trackers_info: Optional[List[TorrentTrackerInfo]]
