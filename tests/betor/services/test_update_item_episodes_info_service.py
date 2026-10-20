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


class TestUpdateItem:
    @pytest.mark.asyncio
    async def test_uses_torrent_files_when_updating_by_item_id(
        self,
        update_item_episodes_info_service: UpdateItemEpisodesInfoService,
    ):
        item = {
            "id": "507f1f77bcf86cd799439011",
            "torrent_name": "Marshals.Uma.História.de.Yellowstone.S02E03.WEB-DL.1080p.x264.DUAL.5.1-STARCKFILMES",
            "magnet_dn": "BAIXARAPIDO.COM-.EPISODIO-03.1080P.MKV.-DUBLADO-DUAL-AUDIO-.Marshals.Uma.História.de.Yellowstone.S02E03.WEB-DL.1080p.x264.DUAL.5.1-STARCKFILMES",
            "torrent_files": [
                "Marshals.Uma.História.de.Yellowstone.S02E03.WEB-DL.1080p.x264.DUAL.5.1-STARCKFILMES.mkv",
                "CANAL TELEGRAM.url",
                "STARCKFILMES.jpg",
            ],
        }
        update_item_episodes_info_service.items_repository.get_by_id = mock.AsyncMock(
            return_value=item
        )
        update_item_episodes_info_service.items_repository.update_item_episodes_info = (
            mock.AsyncMock()
        )

        result = await update_item_episodes_info_service.update_item(item["id"])

        assert result == {"episodes": [{"season": 2, "episode": 3}], "seasons": [2]}
        update_item_episodes_info_service.items_repository.update_item_episodes_info.assert_awaited_once_with(
            item["id"], {"episodes": [{"season": 2, "episode": 3}], "seasons": [2]}
        )


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
                    download_path=None,
                ),
                [],
            ),
            (
                TorrentInfo(
                    torrent_name=None,
                    torrent_files=["the.bear.s01e01.mkv"],
                    torrent_size=None,
                    download_path=None,
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
                    download_path=None,
                ),
                [Episode(season=3, episode=7), Episode(season=3, episode=6)],
            ),
            (
                TorrentInfo(
                    torrent_name=None,
                    torrent_files=[
                        "Youth S01E01-02 WEB-DL 1080p x264 DUAL 5.1.mkv",
                    ],
                    torrent_size=None,
                    download_path=None,
                ),
                [Episode(season=1, episode=1), Episode(season=1, episode=2)],
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
