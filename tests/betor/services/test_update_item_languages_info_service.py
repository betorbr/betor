from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import Item, RawItem
from betor.services import UpdateItemLanguagesInfoService
from betor.types import Languages


@pytest.fixture
def mongodb_client_mock():
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def update_item_languages_info_service(mongodb_client_mock):
    return UpdateItemLanguagesInfoService(mongodb_client_mock)


class TestDeterminesLanguagesInfo:
    @pytest.mark.parametrize(
        (
            "item",
            "raw_item",
            "expected_languages",
        ),
        [
            (
                {},
                {},
                [],
            ),
            (
                {
                    "torrent_name": "The.Magicians.en.S05E05.WEB.H264-XLF[rartv]",
                },
                {"title": "The Magicians", "languages": ["en"]},
                ["en"],
            ),
            (
                {
                    "torrent_name": "The.Magicians.WEB.H264-XLF[rartv]",
                    "torrent_files": [
                        "The.Magicians.en.S05E05.WEB.H264-XLF[rartv].mkv"
                    ],
                },
                {"title": "The Magicians", "languages": ["en"]},
                ["en"],
            ),
            (
                {"torrent_name": "Moana", "torrent_files": ["Moana.DUAL.mkv"]},
                {
                    "title": "Moana o filme",
                    "raw_title": "MOANA O FILME - Dublado",
                    "languages": ["pt", "en"],
                },
                ["pt", "en"],
            ),
            (
                {"torrent_name": "Moana", "torrent_files": ["Moana.DUBLADO.mkv"]},
                {
                    "title": "Moana o filme",
                    "languages": ["pt"],
                },
                ["pt-BR"],
            ),
        ],
        indirect=["item", "raw_item"],
    )
    @pytest.mark.asyncio
    async def test_ok(
        self,
        update_item_languages_info_service: UpdateItemLanguagesInfoService,
        item: Item,
        raw_item: RawItem,
        expected_languages: Languages,
    ):
        result = await update_item_languages_info_service.determines_languages_info(
            item, raw_item
        )
        assert set(result["languages"]) == set(expected_languages)
