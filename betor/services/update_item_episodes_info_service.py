import re
from typing import List

import motor.motor_asyncio

from betor.entities import Episode, EpisodesInfo, TorrentInfo
from betor.repositories import ItemsRepository

DETERMINES_EPISODES_REGEX = re.compile(
    r"[Ss](?P<season>\d{1,2})[EePp]{1,2}(?P<episode>\d{1,2})"
)


class UpdateItemEpisodesInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def update(self, magnet_uri: str, torrent_info: TorrentInfo) -> EpisodesInfo:
        episodes = self.determines_episodes(torrent_info)
        episodes_info = EpisodesInfo(episodes=episodes)
        await self.items_repository.update_episodes_info(magnet_uri, episodes_info)
        return episodes_info

    def determines_episodes(self, torrent_info: TorrentInfo) -> List[Episode]:
        if not torrent_info["torrent_files"]:
            return []
        episodes = []
        for f in torrent_info["torrent_files"]:
            result = DETERMINES_EPISODES_REGEX.search(f)
            if not result:
                continue
            episodes.append(
                Episode(
                    season=int(result.group("season")),
                    episode=int(result.group("episode")),
                )
            )
        return episodes
