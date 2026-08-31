from datetime import datetime
from typing import Literal, TypedDict

TorrentFailurePoint = Literal[
    "update_item_torrent_info", "update_item_torrent_trackers_info"
]


class TorrentFailure(TypedDict):
    occurred_at: datetime
    failure_point: TorrentFailurePoint
