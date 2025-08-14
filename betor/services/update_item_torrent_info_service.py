import tempfile

import libtorrent as lt
import motor.motor_asyncio

from betor.repositories import ItemsRepository
from betor.types import TorrentInfo


class UpdateItemTorrentInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def update(self, magnet_uri: str):
        torrent_info = self.get_info_from_lt_session(magnet_uri)
        await self.items_repository.update_torrent_info(magnet_uri, torrent_info)
        return torrent_info

    def get_info_from_lt_session(self, magnet_uri: str) -> TorrentInfo:
        with tempfile.TemporaryDirectory() as save_path:
            lt_session = lt.session()
            lt_add_torrent_params = lt.parse_magnet_uri(magnet_uri)
            lt_add_torrent_params.save_path = save_path
            lt_torrent_handler = lt_session.add_torrent(lt_add_torrent_params)
            while True:
                lt_torrent_status = lt_torrent_handler.status()
                lt_torrent_info = lt_torrent_handler.torrent_file()
                if lt_torrent_info:
                    lt_file_storage = lt_torrent_info.orig_files()
                    lt_session.pause()
                    return TorrentInfo(
                        torrent_name=lt_file_storage.name(),
                        torrent_num_peers=lt_torrent_status.num_peers,
                        torrent_num_seeds=lt_torrent_status.num_seeds,
                        torrent_files=[
                            lt_file_storage.file_name(i)
                            for i in range(lt_file_storage.num_files())
                        ],
                    )
