from unittest import mock
from datetime import UTC, datetime

import pytest

from betor.celery import tasks
from betor.exceptions import TorrentMetadataTimeout, TorrentTrackersInfoNotFound


def test_torrent_info_worker_success_does_not_record_failure_and_closes_connection():
    mongodb_client = mock.MagicMock()
    service = mock.MagicMock()
    service.update = mock.AsyncMock(return_value={"torrent_name": "ok"})
    service.items_repository.record_torrent_failure = mock.AsyncMock()

    with (
        mock.patch.object(tasks, "get_mongodb_client", return_value=mongodb_client),
        mock.patch.object(tasks, "UpdateItemTorrentInfoService", return_value=service),
    ):
        result = tasks._update_item_torrent_info("magnet-uri")

    assert result == {"torrent_name": "ok"}
    service.items_repository.record_torrent_failure.assert_not_called()
    mongodb_client.close.assert_called_once()


def test_torrent_info_worker_records_metadata_timeout_and_reraises():
    mongodb_client = mock.MagicMock()
    service = mock.MagicMock()
    service.update = mock.AsyncMock(side_effect=TorrentMetadataTimeout())
    service.items_repository.record_torrent_failure = mock.AsyncMock()
    with (
        mock.patch.object(tasks, "get_mongodb_client", return_value=mongodb_client),
        mock.patch.object(tasks, "UpdateItemTorrentInfoService", return_value=service),
    ):
        with pytest.raises(TorrentMetadataTimeout):
            tasks._update_item_torrent_info("magnet-uri")

    service.items_repository.record_torrent_failure.assert_called_once()
    _, failure = service.items_repository.record_torrent_failure.call_args.args
    assert isinstance(failure["occurred_at"], datetime)
    assert failure["occurred_at"].tzinfo == UTC
    assert failure["failure_point"] == "update_item_torrent_info"
    mongodb_client.close.assert_called_once()


def test_tracker_worker_success_does_not_record_failure_and_closes_connection():
    mongodb_client = mock.MagicMock()
    service = mock.MagicMock()
    service.update = mock.AsyncMock(return_value={"torrent_num_seeds": 10})
    service.items_repository.record_torrent_failure = mock.AsyncMock()
    with (
        mock.patch.object(tasks, "get_mongodb_client", return_value=mongodb_client),
        mock.patch.object(
            tasks, "UpdateItemTorrentTrackersInfoService", return_value=service
        ),
    ):
        result = tasks._update_item_torrent_trackers_info("magnet-uri")

    assert result == {"torrent_num_seeds": 10}
    service.items_repository.record_torrent_failure.assert_not_called()
    mongodb_client.close.assert_called_once()


def test_tracker_worker_records_failure_and_reraises():
    mongodb_client = mock.MagicMock()
    service = mock.MagicMock()
    service.update = mock.AsyncMock(side_effect=TorrentTrackersInfoNotFound())
    service.items_repository.record_torrent_failure = mock.AsyncMock()
    with (
        mock.patch.object(tasks, "get_mongodb_client", return_value=mongodb_client),
        mock.patch.object(
            tasks, "UpdateItemTorrentTrackersInfoService", return_value=service
        ),
    ):
        with pytest.raises(TorrentTrackersInfoNotFound):
            tasks._update_item_torrent_trackers_info("magnet-uri")

    service.items_repository.record_torrent_failure.assert_called_once()
    _, failure = service.items_repository.record_torrent_failure.call_args.args
    assert isinstance(failure["occurred_at"], datetime)
    assert failure["occurred_at"].tzinfo == UTC
    assert failure["failure_point"] == "update_item_torrent_trackers_info"
    mongodb_client.close.assert_called_once()
