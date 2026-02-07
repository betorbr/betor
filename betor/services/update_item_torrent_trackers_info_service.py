import motor.motor_asyncio
import torf
from scrapeer import Scraper

from betor.entities import TorrentTrackersInfo
from betor.repositories import ItemsRepository


class UpdateItemTorrentTrackersInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.scraper = Scraper()
        self.items_repository = ItemsRepository(mongodb_client)

    async def update(self, magnet_uri: str):
        torrent_trackers_info = self.get_torrent_trackers_info(magnet_uri)
        await self.items_repository.update_torrent_trackers_info(
            magnet_uri, torrent_trackers_info
        )
        return torrent_trackers_info

    def get_torrent_trackers_info(self, magnet_uri: str) -> TorrentTrackersInfo:
        magnet = torf.Magnet.from_string(magnet_uri)
        results = self.scraper.scrape(
            hashes=[magnet.infohash],
            trackers=list(magnet.tr) or ["udp://tracker.opentrackr.org:1337/announce"],
            timeout=15,
        )
        result = results.get(magnet.infohash, {})
        return TorrentTrackersInfo(
            torrent_num_peers=result.get("leechers"),
            torrent_num_seeds=result.get("seeders"),
        )
