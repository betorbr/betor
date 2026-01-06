import tempfile
from typing import Tuple

import libtorrent as lt
import motor.motor_asyncio

from betor.celery.app import celery_app
from betor.entities import TorrentInfo
from betor.repositories import ItemsRepository
from betor.settings import libtorrent_settings


class UpdateItemTorrentInfoService:
    @classmethod
    def all_trackers_ready(cls, lt_torrent_handler) -> bool:
        return all(map(lambda t: t["fails"] >= 1, lt_torrent_handler.trackers()))

    @classmethod
    def num_peers_seeds(cls, lt_torrent_handler) -> Tuple[int, int]:
        while not cls.all_trackers_ready(lt_torrent_handler):
            pass
        lt_torrent_status = lt_torrent_handler.status()
        return lt_torrent_status.list_peers, lt_torrent_status.list_seeds

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def update(self, magnet_uri: str):
        torrent_info = self.get_info_from_lt_session(magnet_uri)
        await self.items_repository.update_torrent_info(magnet_uri, torrent_info)
        items = await self.items_repository.get_all_by_magnet_uri(magnet_uri)
        for item in items:
            celery_app.signature("update_item_languages_info").delay(item["id"])
        celery_app.signature("update_item_episodes_info").delay(
            magnet_uri=magnet_uri, torrent_info=torrent_info
        )
        return torrent_info

    def get_info_from_lt_session(self, magnet_uri: str) -> TorrentInfo:
        with tempfile.TemporaryDirectory() as save_path:
            lt_session = lt.session(
                {"listen_interfaces": libtorrent_settings.listen_interfaces}
            )
            lt_add_torrent_params = lt.parse_magnet_uri(magnet_uri)
            lt_add_torrent_params.save_path = save_path
            lt_torrent_handler = lt_session.add_torrent(lt_add_torrent_params)
            while True:
                lt_torrent_info = lt_torrent_handler.torrent_file()
                if lt_torrent_info:
                    lt_file_storage = lt_torrent_info.orig_files()
                    lt_torrent_handler.set_download_limit(8)
                    num_peers, num_seeds = self.num_peers_seeds(lt_torrent_handler)
                    torrent_info = TorrentInfo(
                        torrent_name=lt_file_storage.name(),
                        torrent_num_peers=num_peers,
                        torrent_num_seeds=num_seeds,
                        torrent_files=[
                            lt_file_storage.file_name(i)
                            for i in range(lt_file_storage.num_files())
                        ],
                        torrent_size=lt_torrent_info.total_size(),
                    )
                    lt_session.remove_torrent(lt_torrent_handler)
                    return torrent_info
