from unittest import mock

import pytest

from betor.exceptions import TorrentMetadataTimeout, TorrentTrackersInfoNotFound
from betor.services.update_item_torrent_info_service import (
    UpdateItemTorrentInfoService,
)
from betor.services.update_item_torrent_trackers_info_service import (
    UpdateItemTorrentTrackersInfoService,
)
from betor.settings import libtorrent_settings


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
