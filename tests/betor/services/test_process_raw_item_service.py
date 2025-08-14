from unittest import mock

import motor.motor_asyncio
import pytest
from faker import Faker

from betor.entities import BaseItem, RawItem
from betor.enums import ItemType
from betor.repositories import ItemsRepository, RawItemsRepository
from betor.services import DeterminesIMDbTMDBIdsService, ProcessRawItemService

MAGNET_LINK_1 = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny&tr=udp%3A%2F%2Fexplodie.org%3A6969&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Ftracker.empire-js.us%3A1337&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337&tr=wss%3A%2F%2Ftracker.btorrent.xyz&tr=wss%3A%2F%2Ftracker.fastcast.nz&tr=wss%3A%2F%2Ftracker.openwebtorrent.com&ws=https%3A%2F%2Fwebtorrent.io%2Ftorrents%2F&xs=https%3A%2F%2Fwebtorrent.io%2Ftorrents%2Fbig-buck-bunny.torrent"


@pytest.fixture
def mongodb_client_mock():
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def process_raw_item_service(mongodb_client_mock):
    with (
        mock.patch(
            "betor.services.process_raw_item_service.RawItemsRepository",
            new_callable=mock.MagicMock,
            spec=RawItemsRepository,
        ),
        mock.patch(
            "betor.services.process_raw_item_service.ItemsRepository",
            new_callable=mock.MagicMock,
            spec=ItemsRepository,
        ),
        mock.patch(
            "betor.services.process_raw_item_service.DeterminesIMDbTMDBIdsService",
            new_callable=mock.MagicMock,
            spec=DeterminesIMDbTMDBIdsService,
        ),
    ):
        yield ProcessRawItemService(mongodb_client_mock)


class TestProcess:
    @pytest.mark.parametrize(
        "raw_item",
        [
            {
                "magnet_uris": [
                    "magnet:?xt=urn:btih:abcf1eaa3eb970de111e83be6cdd57260c1664ec"
                ]
            }
        ],
        indirect=["raw_item"],
    )
    @pytest.mark.asyncio
    async def test_ok(
        self,
        raw_item: RawItem,
        fake: Faker,
        process_raw_item_service: ProcessRawItemService,
    ):
        imdb_id = fake.numerify("tt########")
        tmdb_id = "12345678"
        process_raw_item_service.raw_items_repository.get.return_value = raw_item  # type: ignore[attr-defined]
        process_raw_item_service.determines_imdb_tmdb_ids_service.determines.return_value = tuple(  # type: ignore[attr-defined]
            [
                imdb_id,
                tmdb_id,
                ItemType.movie,
            ]
        )
        with mock.patch.object(
            process_raw_item_service,
            "process_raw_item_magnet_uri",
            new_callable=mock.AsyncMock,
            return_value={"id": None},
        ):
            assert await process_raw_item_service.process(
                raw_item["provider_slug"], raw_item["provider_url"]
            ) == {
                "base_item": {
                    "provider_slug": raw_item["provider_slug"],
                    "provider_url": raw_item["provider_url"],
                    "imdb_id": imdb_id,
                    "tmdb_id": tmdb_id,
                    "item_type": ItemType.movie,
                },
                "items": [{"id": None}],
            }

    @pytest.mark.parametrize("raw_item", [{}], indirect=["raw_item"])
    @pytest.mark.asyncio
    async def test_none_ids(
        self,
        raw_item: RawItem,
        fake: Faker,
        process_raw_item_service: ProcessRawItemService,
    ):
        process_raw_item_service.raw_items_repository.get.return_value = raw_item  # type: ignore[attr-defined]
        process_raw_item_service.determines_imdb_tmdb_ids_service.determines.return_value = tuple(  # type: ignore[attr-defined]
            [
                None,
                None,
                None,
            ]
        )
        with mock.patch.object(
            process_raw_item_service,
            "process_raw_item_magnet_uri",
            new_callable=mock.AsyncMock,
            return_value={"id": None},
        ) as process_raw_item_magnet_uri:
            assert await process_raw_item_service.process(
                raw_item["provider_slug"], raw_item["provider_url"]
            ) == {
                "base_item": {
                    "provider_slug": raw_item["provider_slug"],
                    "provider_url": raw_item["provider_url"],
                    "imdb_id": None,
                    "tmdb_id": None,
                    "item_type": None,
                },
                "items": [],
            }
            process_raw_item_magnet_uri.assert_not_called()


class TestProcessRawItemMagnetURI:
    @pytest.mark.parametrize(
        "raw_item", [{"magnet_uris": [MAGNET_LINK_1]}], indirect=["raw_item"]
    )
    @pytest.mark.asyncio
    async def test_ok(
        self, raw_item: RawItem, process_raw_item_service: ProcessRawItemService
    ):
        base_item = BaseItem(
            provider_slug=raw_item["provider_slug"],
            provider_url=raw_item["provider_url"],
            imdb_id=None,
            tmdb_id=None,
            item_type=None,
        )
        with mock.patch(
            "betor.services.process_raw_item_service.celery_app.signature"
        ) as signature_mock:
            result = await process_raw_item_service.process_raw_item_magnet_uri(
                raw_item,
                base_item,
                MAGNET_LINK_1,
            )
        assert result == process_raw_item_service.items_repository.get.return_value  # type: ignore[attr-defined]
        item = process_raw_item_service.items_repository.insert_or_update.call_args[0][  # type: ignore[attr-defined]
            0
        ]
        assert item
        assert item["magnet_uri"] == MAGNET_LINK_1
        assert item["magnet_xt"] == "urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
        assert item["magnet_dn"] == "Big Buck Bunny"
        signature_mock.assert_called_once_with("update_item_torrent_info")
        signature_mock.return_value.delay.assert_called_once_with(MAGNET_LINK_1)

    @pytest.mark.parametrize(
        "magnet_uri",
        [
            "https://example.com",
            "https://example.com?foo=bar",
            "magnet://example.com",
            "magnet:?foo=bar",
        ],
    )
    @pytest.mark.asyncio
    async def test_invalid_magnet_uri(
        self, process_raw_item_service: ProcessRawItemService, magnet_uri: str
    ):
        raw_item = mock.MagicMock(spec=RawItem)
        base_item = mock.MagicMock(spec=BaseItem)
        result = await process_raw_item_service.process_raw_item_magnet_uri(
            raw_item,
            base_item,
            magnet_uri,
        )
        assert result is None
