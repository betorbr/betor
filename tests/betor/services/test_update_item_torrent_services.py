from unittest import mock

import pytest

from betor.exceptions import TorrentMetadataTimeout, TorrentTrackersInfoNotFound
from betor.services.update_item_torrent_info_service import (
    UpdateItemTorrentInfoService,
)
from betor.services.update_item_torrent_trackers_info_service import (
    UpdateItemTorrentTrackersInfoService,
)
from betor.settings import itorrent_settings, libtorrent_settings


@pytest.mark.asyncio
async def test_metadata_service_update_recalculates_health_on_success():
    service = UpdateItemTorrentInfoService(mock.MagicMock())
    torrent_info = {
        "torrent_name": "name",
        "torrent_files": ["file.mkv"],
        "torrent_size": 123,
        "download_path": None,
    }
    service.get_info_from_lt_session = mock.MagicMock(return_value=torrent_info)
    service.items_repository.update_torrent_info = mock.AsyncMock()
    service.items_repository.maintain_torrent_health = mock.AsyncMock()
    service.items_repository.get_all_by_magnet_uri = mock.AsyncMock(return_value=[])

    with mock.patch("betor.services.update_item_torrent_info_service.celery_app"):
        result = await service.update("magnet-uri")

    assert result == torrent_info
    service.items_repository.update_torrent_info.assert_awaited_once_with(
        "magnet-uri", torrent_info
    )
    service.items_repository.maintain_torrent_health.assert_awaited_once_with(
        "magnet-uri"
    )


@pytest.mark.asyncio
async def test_tracker_service_update_recalculates_health_on_success():
    service = UpdateItemTorrentTrackersInfoService(mock.MagicMock())
    trackers_info = {
        "torrent_num_peers": 3,
        "torrent_num_seeds": 7,
    }
    service.get_torrent_trackers_info = mock.MagicMock(return_value=trackers_info)
    service.items_repository.update_torrent_trackers_info = mock.AsyncMock()
    service.items_repository.maintain_torrent_health = mock.AsyncMock()

    result = await service.update("magnet-uri")

    assert result == trackers_info
    service.items_repository.update_torrent_trackers_info.assert_awaited_once_with(
        "magnet-uri", trackers_info
    )
    service.items_repository.maintain_torrent_health.assert_awaited_once_with(
        "magnet-uri"
    )


def test_tracker_service_raises_domain_exception_for_missing_result():
    service = UpdateItemTorrentTrackersInfoService(mock.MagicMock())
    with mock.patch.object(service, "get_best_torrent_tracker_info", return_value=None):
        with pytest.raises(TorrentTrackersInfoNotFound):
            service.get_torrent_trackers_info(
                "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
            )


def test_metadata_service_raises_domain_exception_at_configured_timeout():
    service = UpdateItemTorrentInfoService(mock.MagicMock())
    session = mock.MagicMock()
    handler = session.add_torrent.return_value
    handler.has_metadata.return_value = False
    with (
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.session",
            return_value=session,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.parse_magnet_uri",
            return_value=mock.MagicMock(),
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.monotonic",
            side_effect=[0, 6],
        ),
        mock.patch("betor.services.update_item_torrent_info_service.sleep"),
        mock.patch.object(libtorrent_settings, "metadata_timeout", 5),
    ):
        with pytest.raises(TorrentMetadataTimeout):
            service.get_info_from_lt_session("magnet-uri")

    session.remove_torrent.assert_called_once_with(handler)


def _build_libtorrent_happy_path_mocks():
    session = mock.MagicMock()
    handler = session.add_torrent.return_value
    handler.has_metadata.return_value = True
    lt_torrent_info = mock.MagicMock()
    handler.torrent_file.return_value = lt_torrent_info
    lt_file_storage = mock.MagicMock()
    lt_torrent_info.orig_files.return_value = lt_file_storage
    lt_file_storage.name.return_value = "test.torrent"
    lt_file_storage.num_files.return_value = 1
    lt_file_storage.file_name.return_value = "test.mkv"
    lt_torrent_info.total_size.return_value = 123
    lt_torrent_info.info_hash.return_value = "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
    created_torrent = mock.MagicMock()
    created_torrent.generate.return_value = {}
    return session, lt_torrent_info, created_torrent, handler


def test_metadata_service_sets_upload_timestamp_when_itorrent_upload_succeeds():
    service = UpdateItemTorrentInfoService(mock.MagicMock())
    session, _lt_torrent_info, created_torrent, handler = (
        _build_libtorrent_happy_path_mocks()
    )

    with (
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.session",
            return_value=session,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.parse_magnet_uri",
            return_value=mock.MagicMock(),
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.create_torrent",
            return_value=created_torrent,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.bencode",
            return_value=b"torrent-content",
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.monotonic",
            return_value=0,
        ),
        mock.patch.object(itorrent_settings, "upload_enabled", True),
        mock.patch.object(
            service, "upload_to_itorrent", return_value=True
        ) as upload_mock,
    ):
        torrent_info = service.get_info_from_lt_session("magnet-uri")

    upload_mock.assert_called_once_with(b"torrent-content")
    assert torrent_info["itorrent_uploaded_at"] is not None
    session.remove_torrent.assert_called_once_with(handler)


def test_metadata_service_keeps_upload_timestamp_null_when_itorrent_upload_fails():
    service = UpdateItemTorrentInfoService(mock.MagicMock())
    session, _lt_torrent_info, created_torrent, _handler = (
        _build_libtorrent_happy_path_mocks()
    )

    with (
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.session",
            return_value=session,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.parse_magnet_uri",
            return_value=mock.MagicMock(),
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.create_torrent",
            return_value=created_torrent,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.bencode",
            return_value=b"torrent-content",
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.monotonic",
            return_value=0,
        ),
        mock.patch.object(itorrent_settings, "upload_enabled", True),
        mock.patch.object(service, "upload_to_itorrent", return_value=False),
    ):
        torrent_info = service.get_info_from_lt_session("magnet-uri")

    assert torrent_info["itorrent_uploaded_at"] is None


def test_metadata_service_does_not_call_itorrent_upload_when_disabled():
    service = UpdateItemTorrentInfoService(mock.MagicMock())
    session, _lt_torrent_info, created_torrent, _handler = (
        _build_libtorrent_happy_path_mocks()
    )

    with (
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.session",
            return_value=session,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.parse_magnet_uri",
            return_value=mock.MagicMock(),
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.create_torrent",
            return_value=created_torrent,
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.lt.bencode",
            return_value=b"torrent-content",
        ),
        mock.patch(
            "betor.services.update_item_torrent_info_service.monotonic",
            return_value=0,
        ),
        mock.patch.object(itorrent_settings, "upload_enabled", False),
        mock.patch.object(service, "upload_to_itorrent") as upload_mock,
    ):
        torrent_info = service.get_info_from_lt_session("magnet-uri")

    upload_mock.assert_not_called()
    assert torrent_info["itorrent_uploaded_at"] is None


def test_upload_itorrent_accepts_success_page_with_torrent_url():
    from betor.services.update_item_torrent_info_service import (
        upload_torrent_to_itorrent,
    )

    hash_value = "ED0E37901D11FABDEF74134260894A26B1FABCD8"
    success_html = f"""
    <html>
      <body>
        <a href="/torrent/{hash_value}.torrent">Download</a>
      </body>
    </html>
    """

    with (
        mock.patch(
            "betor.services.update_item_torrent_info_service.requests.post"
        ) as post_mock,
        mock.patch(
            "betor.services.update_item_torrent_info_service.verify_itorrent_download_exists",
            return_value=True,
        ) as verify_mock,
    ):
        post_mock.return_value.status_code = 200
        post_mock.return_value.raise_for_status.return_value = None
        post_mock.return_value.text = success_html

        success, info_hash, response_text = upload_torrent_to_itorrent(
            b"torrent-data",
            url="https://itorrents.net/upload.php",
            timeout=10,
        )

    verify_mock.assert_called_once_with(hash_value, timeout=10)
    assert success is True
    assert info_hash == hash_value
    assert response_text == success_html


def test_verify_itorrent_download_exists_tries_upper_and_lowercase_hashes():
    from betor.services.update_item_torrent_info_service import (
        verify_itorrent_download_exists,
    )

    with mock.patch(
        "betor.services.update_item_torrent_info_service.requests.head"
    ) as head_mock:
        head_mock.side_effect = [
            mock.Mock(status_code=520, url="https://itorrents.net/torrent/abc.torrent"),
            mock.Mock(status_code=200, url="https://itorrents.net/torrent/ABC.torrent"),
        ]

        assert verify_itorrent_download_exists("abc", timeout=10) is True
        assert head_mock.call_count == 2
        assert head_mock.call_args_list[0].args[0] == "https://itorrents.net/torrent/ABC.torrent"
        assert head_mock.call_args_list[1].args[0] == "https://itorrents.net/torrent/abc.torrent"


def test_upload_itorrent_rejects_error_no_data_response():
    from betor.services.update_item_torrent_info_service import (
        upload_torrent_to_itorrent,
    )

    with mock.patch(
        "betor.services.update_item_torrent_info_service.requests.post"
    ) as post_mock:
        post_mock.return_value.status_code = 200
        post_mock.return_value.raise_for_status.return_value = None
        post_mock.return_value.text = "error, no data"

        success, info_hash, response_text = upload_torrent_to_itorrent(
            b"torrent-data",
            url="http://itorrents.net/autoupload.php",
            timeout=10,
        )

    assert success is False
    assert info_hash is None
    assert response_text == "error, no data"
