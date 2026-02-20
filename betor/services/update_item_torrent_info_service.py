import tempfile
from time import sleep

import fsspec
import libtorrent as lt
import motor.motor_asyncio

from betor.celery.app import celery_app
from betor.entities import TorrentInfo
from betor.repositories import ItemsRepository
from betor.settings import libtorrent_settings, store_torrent_file_settings


class UpdateItemTorrentInfoService:
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
            while not lt_torrent_handler.has_metadata():
                sleep(1)
            lt_torrent_info = lt_torrent_handler.torrent_file()
            lt_file_storage = lt_torrent_info.orig_files()
            torrent_file = lt.create_torrent(lt_torrent_info)
            download_path = None
            if store_torrent_file_settings.enabled:
                download_path = f"{lt_torrent_info.info_hash()}.torrent"
                with fsspec.open(
                    f"{store_torrent_file_settings.save_url}/{download_path}", "wb"
                ) as f:
                    f.write(lt.bencode(torrent_file.generate()))
            torrent_info = TorrentInfo(
                torrent_name=lt_file_storage.name(),
                torrent_files=[
                    lt_file_storage.file_name(i)
                    for i in range(lt_file_storage.num_files())
                ],
                torrent_size=lt_torrent_info.total_size(),
                download_path=download_path,
            )
            lt_session.remove_torrent(lt_torrent_handler)
            return torrent_info
