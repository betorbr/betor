import re
from typing import List, Optional

import motor.motor_asyncio

from betor.entities import Episode, EpisodesInfo, TorrentInfo
from betor.exceptions import ItemNotFound
from betor.repositories import ItemsRepository

DETERMINES_EPISODES_REGEX = re.compile(r"(?i)S(?P<season>\d{1,2})E(?P<episode>\d{1,2})")
DETERMINES_SEASON_REGEX = re.compile(r"(?i)S(?P<season>\d{1,2})")


class UpdateItemEpisodesInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def update_item(self, item_id: str) -> EpisodesInfo:
        item = await self.items_repository.get_by_id(item_id)
        if not item:
            raise ItemNotFound()
        torrent_info = TorrentInfo(
            torrent_name=item.get("torrent_name"),
            torrent_files=item.get("torrent_files"),
            torrent_size=item.get("torrent_size"),
            download_path=item.get("download_path"),
        )
        episodes = self.determines_episodes(torrent_info)
        seasons = self.determines_seasons(
            item.get("torrent_name") or item.get("magnet_dn"),
            episodes,
        )
        episodes_info = EpisodesInfo(episodes=episodes, seasons=seasons)
        assert item["id"]
        await self.items_repository.update_item_episodes_info(item["id"], episodes_info)
        return episodes_info

    async def update_magnet_uri(
        self, magnet_uri: str, torrent_info: TorrentInfo
    ) -> EpisodesInfo:
        episodes = self.determines_episodes(torrent_info)
        seasons = self.determines_seasons(torrent_info["torrent_name"], episodes)
        episodes_info = EpisodesInfo(episodes=episodes, seasons=seasons)
        await self.items_repository.update_episodes_info(magnet_uri, episodes_info)
        return episodes_info

    def determines_episodes(self, torrent_info: TorrentInfo) -> List[Episode]:
        if not torrent_info["torrent_files"]:
            return []
        episodes = []
        for f in torrent_info["torrent_files"]:
            for result in DETERMINES_EPISODES_REGEX.finditer(f):
                season = int(result.group("season"))
                start_episode = int(result.group("episode"))
                suffix = f[result.end() :]  # noqa: E203
                parsed_episodes = [start_episode]
                pos = 0
                while pos < len(suffix):
                    match = re.match(
                        r"(?i)^([-_]+E?|E)(?P<episode>\d{1,2})(?!\d)", suffix[pos:]
                    )
                    if not match:
                        break
                    parsed_episodes.append(int(match.group("episode")))
                    pos += match.end()

                episode_numbers = list(
                    range(min(parsed_episodes), max(parsed_episodes) + 1)
                )
                for episode_number in episode_numbers:
                    episodes.append(Episode(season=season, episode=episode_number))
        return episodes

    def determines_seasons(
        self,
        torrent_name: Optional[str] = None,
        episodes: Optional[List[Episode]] = None,
    ) -> List[int]:
        seasons = []
        if torrent_name:
            result = DETERMINES_SEASON_REGEX.search(torrent_name)
            if result:
                seasons.append(int(result.group("season")))
        if not episodes:
            return seasons
        for e in episodes:
            if e["season"] in seasons:
                continue
            seasons.append(e["season"])
        return seasons
