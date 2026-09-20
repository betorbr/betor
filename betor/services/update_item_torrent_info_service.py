import re
import tempfile
from datetime import datetime
from logging import getLogger
from time import monotonic, sleep

import fsspec
import libtorrent as lt
import motor.motor_asyncio
import requests

from betor.celery.app import celery_app
from betor.entities import TorrentInfo
from betor.exceptions import TorrentMetadataTimeout
from betor.repositories import ItemsRepository
from betor.settings import (
    itorrent_settings,
    libtorrent_settings,
    store_torrent_file_settings,
)

logger = getLogger(__name__)


def extract_itorrent_info_hash(response_text: str) -> str | None:
    if not response_text or not response_text.strip():
        return None

    for pattern in (
        r"/torrent/([A-Fa-f0-9]{40})\.torrent",
        r"[A-Fa-f0-9]{40}",
    ):
        match = re.search(pattern, response_text)
        if match:
            info_hash = match.group(1) if pattern.startswith("/torrent/") else match.group(0)
            if len(info_hash) == 40 and all(
                c in "0123456789abcdefABCDEF" for c in info_hash
            ):
                return info_hash

    response_lines = [
        line.strip() for line in response_text.splitlines() if line.strip()
    ]
    for line in reversed(response_lines):
        candidate = line[:40]
        if len(candidate) == 40 and all(
            c in "0123456789abcdefABCDEF" for c in candidate
        ):
            return candidate

    return None


def verify_itorrent_download_exists(
    info_hash: str,
    *,
    base_url: str = itorrent_settings.public_download_base_url,
    timeout: int = 10,
) -> bool:
    if not info_hash:
        return False

    for variant in (info_hash.upper(), info_hash.lower()):
        url = f"{base_url.rstrip('/')}/{variant}.torrent"
        try:
            response = requests.head(url, allow_redirects=True, timeout=timeout)
            if response.status_code in {200, 206, 301, 302, 303, 307, 308}:
                logger.info(
                    "iTorrent torrent found via HEAD; hash=%s status=%s final_url=%s",
                    info_hash,
                    response.status_code,
                    response.url,
                )
                return True
            logger.warning(
                "iTorrent torrent HEAD check failed; hash=%s url=%s status=%s",
                info_hash,
                url,
                response.status_code,
            )
        except requests.RequestException as exc:
            logger.warning("iTorrent torrent HEAD check failed for %s: %s", url, exc)
    return False


def upload_torrent_to_itorrent(
    torrent_file_bytes: bytes,
    *,
    url: str,
    timeout: int = 10,
) -> tuple[bool, str | None, str]:
    try:
        response = requests.post(
            url,
            files={
                "torrent": (
                    "upload.torrent",
                    torrent_file_bytes,
                    "application/x-bittorrent",
                )
            },
            timeout=timeout,
        )
        response.raise_for_status()
        info_hash = extract_itorrent_info_hash(response.text)
        if info_hash is None:
            logger.warning(
                "iTorrent upload did not return a valid info hash; status=%s response=%s",
                response.status_code,
                response.text[:500],
            )
            return False, None, response.text

        if not verify_itorrent_download_exists(info_hash, timeout=timeout):
            logger.warning(
                "iTorrent upload returned a hash but the torrent is not publicly available; hash=%s response=%s",
                info_hash,
                response.text[:500],
            )
            return False, info_hash, response.text

        return True, info_hash, response.text
    except requests.RequestException as exc:
        logger.warning("iTorrent upload request failed: %s", exc)
        return False, None, str(exc)


class UpdateItemTorrentInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def update(self, magnet_uri: str):
        torrent_info = self.get_info_from_lt_session(magnet_uri)
        await self.items_repository.update_torrent_info(magnet_uri, torrent_info)
        await self.items_repository.maintain_torrent_health(magnet_uri)
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
            timeout_at = monotonic() + libtorrent_settings.metadata_timeout
            while not lt_torrent_handler.has_metadata():
                if monotonic() >= timeout_at:
                    lt_session.remove_torrent(lt_torrent_handler)
                    raise TorrentMetadataTimeout(
                        f"Timed out retrieving torrent metadata for {magnet_uri}"
                    )
                sleep(min(1, max(0, timeout_at - monotonic())))
            lt_torrent_info = lt_torrent_handler.torrent_file()
            if lt_torrent_info is None:
                lt_session.remove_torrent(lt_torrent_handler)
                raise ValueError(
                    f"Could not retrieve torrent metadata for {magnet_uri}"
                )
            lt_file_storage = lt_torrent_info.orig_files()
            torrent_file = lt.create_torrent(lt_torrent_info)
            torrent_bytes = lt.bencode(torrent_file.generate())
            download_path = None
            if store_torrent_file_settings.enabled:
                download_path = f"{lt_torrent_info.info_hash()}.torrent"
                with fsspec.open(
                    f"{store_torrent_file_settings.save_url}/{download_path}", "wb"
                ) as f:
                    f.write(torrent_bytes)

            itorrent_uploaded_at = None
            if itorrent_settings.upload_enabled:
                if self.upload_to_itorrent(torrent_bytes):
                    itorrent_uploaded_at = datetime.now()
                else:
                    logger.warning(
                        "Could not upload torrent metadata to iTorrent",
                        extra={"magnet_uri": magnet_uri},
                    )

            torrent_info = TorrentInfo(
                torrent_name=lt_file_storage.name(),
                torrent_files=[
                    lt_file_storage.file_name(i)
                    for i in range(lt_file_storage.num_files())
                ],
                torrent_size=lt_torrent_info.total_size(),
                download_path=download_path,
                itorrent_uploaded_at=itorrent_uploaded_at,
            )
            lt_session.remove_torrent(lt_torrent_handler)
            return torrent_info

    @staticmethod
    def upload_to_itorrent(torrent_file_bytes: bytes) -> bool:
        success, _info_hash, _response_text = upload_torrent_to_itorrent(
            torrent_file_bytes,
            url=itorrent_settings.autoupload_url,
            timeout=10,
        )
        return success
