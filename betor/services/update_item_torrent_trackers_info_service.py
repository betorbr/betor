from typing import Dict, Optional

import motor.motor_asyncio
import torf
from scrapeer import Scraper

from betor.entities import TorrentTrackersInfo
from betor.exceptions import TorrentTrackersInfoNotFound
from betor.repositories import ItemsRepository
from betor.utils import extract_magnet_info_hash


class UpdateItemTorrentTrackersInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.scraper = Scraper()
        self.items_repository = ItemsRepository(mongodb_client)

    async def update(self, magnet_uri: str):
        torrent_trackers_info = self.get_torrent_trackers_info(magnet_uri)
        await self.items_repository.update_torrent_trackers_info(
            magnet_uri, torrent_trackers_info
        )
        await self.items_repository.maintain_torrent_health(magnet_uri)
        return torrent_trackers_info

    def get_best_torrent_tracker_info(
        self, magnet: torf.Magnet
    ) -> Optional[Dict[str, int]]:
        result: Optional[Dict[str, int]] = None
        trackers = set(
            list(magnet.tr)
            + [
                "udp://tracker.opentrackr.org:1337/announce",
                "udp://open.stealth.si:80/announce",
                "udp://tracker-udp.gbitt.info:80/announce",
                "http://ipv4announce.sktorrent.eu:6969/announce",
                "udp://tracker.torrent.eu.org:451/announce",
                "udp://evan.im:6969/announce",
            ]
        )
        for tracker in trackers:
            results = self.scraper.scrape(
                hashes=[magnet.infohash, magnet.infohash.lower()],
                trackers=[tracker],
                timeout=5,
            )
            r = results.get(magnet.infohash, {}) or results.get(
                magnet.infohash.lower(), {}
            )
            print(f"Tracker: {tracker}, Result: {r}")
            if not result or r.get("seeders", 0) > result.get("seeders", 0):
                result = r
        return result

    def get_torrent_trackers_info(self, magnet_uri: str) -> TorrentTrackersInfo:
        magnet = torf.Magnet.from_string(magnet_uri)
        parsed_info_hash = extract_magnet_info_hash(magnet_uri)
        if parsed_info_hash:
            magnet.infohash = parsed_info_hash
        result = self.get_best_torrent_tracker_info(magnet)
        if not result:
            raise TorrentTrackersInfoNotFound(
                "No result found for magnet URI: {}".format(magnet_uri)
            )
        return TorrentTrackersInfo(
            torrent_num_peers=result.get("leechers"),
            torrent_num_seeds=result.get("seeders"),
        )
