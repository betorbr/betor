from typing import List
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import Episode, TorrentInfo
from betor.services import UpdateItemEpisodesInfoService


@pytest.fixture
def mongodb_client_mock():
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def update_item_episodes_info_service(mongodb_client_mock):
    return UpdateItemEpisodesInfoService(mongodb_client_mock)


class TestDeterminesEpisodes:
    @pytest.mark.parametrize(
        (
            "torrent_info",
            "expected",
        ),
        [
            (
                TorrentInfo(
                    torrent_name=None,
                    torrent_files=None,
                    torrent_size=None,
                ),
                [],
            ),
            (
                TorrentInfo(
                    torrent_name=None,
                    torrent_files=["the.bear.s01e01.mkv"],
                    torrent_size=None,
                ),
                [Episode(season=1, episode=1)],
            ),
            (
                TorrentInfo(
                    torrent_name=None,
                    torrent_files=[
                        "Foundation.S03E07.1080p.WEB-DL.DUAL.5.1.mkv",
                        "Foundation.S03E06.1080p.WEB-DL.DUAL.5.1.mkv",
                    ],
                    torrent_size=None,
                ),
                [Episode(season=3, episode=7), Episode(season=3, episode=6)],
            ),
        ],
    )
    def test_ok(
        self,
        update_item_episodes_info_service: UpdateItemEpisodesInfoService,
        torrent_info: TorrentInfo,
        expected,
    ):
        assert (
            update_item_episodes_info_service.determines_episodes(torrent_info)
            == expected
        )


class TestDeterminesSeasons:
    @pytest.mark.parametrize(
        (
            "torrent_name",
            "episodes",
            "expected",
        ),
        [
            ("", [], []),
            ("round_6.s01", [], [1]),
            ("foo", [Episode(season=1, episode=1)], [1]),
            ("foo", [Episode(season=1, episode=1), Episode(season=1, episode=2)], [1]),
        ],
    )
    def test_ok(
        self,
        update_item_episodes_info_service: UpdateItemEpisodesInfoService,
        torrent_name: str,
        episodes: List[Episode],
        expected,
    ):
        assert (
            update_item_episodes_info_service.determines_seasons(torrent_name, episodes)
            == expected
        )
