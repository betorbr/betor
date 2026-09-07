from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Generator, cast
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import RawItem, TorrentFailure
from betor.repositories import ItemsRepository


@pytest.fixture()
def mongodb_client_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture()
def collection_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorCollection)


@pytest.fixture()
def items_repository(
    mongodb_client_mock, collection_mock
) -> Generator[ItemsRepository]:
    with mock.patch.object(
        ItemsRepository,
        "collection",
        new_callable=mock.PropertyMock,
        return_value=collection_mock,
    ):
        yield ItemsRepository(mongodb_client_mock)


class TestCalculateHash:
    def test_ok(self):
        with mock.patch.object(ItemsRepository, "build_data", return_value={}):
            assert (
                ItemsRepository.calculate_hash(mock.MagicMock(spec=RawItem)) == 53616175
            )


class TestBuildData:
    @pytest.mark.parametrize(
        (
            "item",
            "expected",
        ),
        [
            (
                {"provider_slug": "slug"},
                [
                    (
                        "provider_slug",
                        "slug",
                    ),
                ],
            ),
            (
                {"provider_slug": "slug", "languages": ["pt"]},
                [
                    (
                        "provider_slug",
                        "slug",
                    ),
                ],
            ),
        ],
    )
    def test_ok(self, item, expected):
        assert ItemsRepository.build_data(item) == OrderedDict(expected)


class TestGet:
    @pytest.mark.asyncio
    async def test_ok(
        self,
        items_repository: ItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(
            return_value={
                "_id": "1234",
                "provider_slug": "slug",
                "provider_url": "http://example.com",
                "magnet_uri": "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny&tr=udp%3A%2F%2Fexplodie.org%3A6969&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Ftracker.empire-js.us%3A1337&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337&tr=wss%3A%2F%2Ftracker.btorrent.xyz&tr=wss%3A%2F%2Ftracker.fastcast.nz&tr=wss%3A%2F%2Ftracker.openwebtorrent.com&ws=https%3A%2F%2Fwebtorrent.io%2Ftorrents%2F&xs=https%3A%2F%2Fwebtorrent.io%2Ftorrents%2Fbig-buck-bunny.torrent",
                "magnet_xt": "urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c",
            }
        )
        result = await items_repository.get(
            "slug",
            "http://example.com",
            "urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c",
        )
        assert result
        assert result["id"] == "1234"

    @pytest.mark.asyncio
    async def test_not_found(
        self,
        items_repository: ItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(return_value=None)
        assert (
            await items_repository.get(
                "slug",
                "http://example.com",
                "urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c",
            )
            is None
        )


class TestInsertOrUpdateItem:
    @pytest.mark.asyncio
    async def test_inserted_ok(self, items_repository: ItemsRepository):
        with (
            mock.patch.object(
                items_repository,
                "get",
                new_callable=mock.AsyncMock,
                return_value=None,
            ),
            mock.patch.object(
                items_repository, "insert", new_callable=mock.AsyncMock
            ) as insert_item_mock,
        ):
            result = await items_repository.insert_or_update(
                mock.MagicMock(spec=RawItem)
            )
            assert result == "inserted"
            insert_item_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_updated_ok(self, items_repository: ItemsRepository):
        with (
            mock.patch.object(
                items_repository,
                "get",
                new_callable=mock.AsyncMock,
                return_value={"hash": "123"},
            ),
            mock.patch(
                "betor.repositories.items_repository.ItemsRepository.calculate_hash",
                return_value="321",
            ),
            mock.patch.object(
                items_repository, "update", new_callable=mock.AsyncMock
            ) as update_item_mock,
        ):
            result = await items_repository.insert_or_update(
                mock.MagicMock(spec=RawItem)
            )
            assert result == "updated"
            update_item_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_change_ok(self, items_repository: ItemsRepository):
        with (
            mock.patch.object(
                items_repository,
                "get",
                new_callable=mock.AsyncMock,
                return_value={"hash": "123"},
            ),
            mock.patch(
                "betor.repositories.items_repository.ItemsRepository.calculate_hash",
                return_value="123",
            ),
        ):
            result = await items_repository.insert_or_update(
                mock.MagicMock(spec=RawItem)
            )
            assert result == "no_change"


class TestDumpAllItems:
    @pytest.mark.asyncio
    async def test_ok(self, items_repository: ItemsRepository, collection_mock):
        collection_mock.find = mock.MagicMock(
            return_value=mock.MagicMock(
                to_list=mock.AsyncMock(
                    return_value=[
                        {
                            "_id": "1234",
                            "provider_slug": "slug",
                            "provider_url": "http://example.com",
                            "magnet_uri": "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c",
                            "magnet_xt": "urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c",
                        }
                    ]
                )
            )
        )

        with mock.patch(
            "betor.repositories.items_repository.perf_counter",
            side_effect=[1.0, 1.5],
        ):
            duration, items = await items_repository.dump_all_items()

        assert duration == 0.5
        assert len(items) == 1
        assert items[0]["id"] == "1234"
        assert items[0]["provider_slug"] == "slug"


class TestRecordTorrentFailure:
    @pytest.mark.asyncio
    async def test_maintain_torrent_health_recalculates_without_new_failure(
        self, items_repository: ItemsRepository, collection_mock
    ):
        collection_mock.update_many = mock.AsyncMock()
        fixed_now = datetime(2026, 9, 7, 12, 0, 0)

        with mock.patch.object(ItemsRepository, "_utc_now", return_value=fixed_now):
            await items_repository.maintain_torrent_health("magnet-uri")

        collection_mock.update_many.assert_awaited_once()
        query, pipeline = collection_mock.update_many.call_args.args
        assert query == {"magnet_uri": "magnet-uri"}

        history_filter = pipeline[0]["$set"]["torrent_failure_history"]["$filter"]
        assert history_filter["input"] == {"$ifNull": ["$torrent_failure_history", []]}

        day_format = pipeline[1]["$set"]["torrent_failure_days"]["$size"]["$setUnion"][0][
            "$map"
        ]["in"]["$dateToString"]
        assert day_format == {
            "format": "%Y-%m-%d",
            "date": "$$failure.occurred_at",
            "timezone": "UTC",
        }

    @pytest.mark.asyncio
    async def test_maintain_torrent_health_uses_rolling_window_bounds(
        self, items_repository: ItemsRepository, collection_mock
    ):
        collection_mock.update_many = mock.AsyncMock()
        fixed_now = datetime(2026, 9, 7, 12, 0, 0)

        with mock.patch.object(ItemsRepository, "_utc_now", return_value=fixed_now):
            await items_repository.maintain_torrent_health("magnet-uri")

        _, pipeline = collection_mock.update_many.call_args.args
        window_cond = pipeline[0]["$set"]["torrent_failure_history"]["$filter"]["cond"][
            "$and"
        ]
        assert window_cond[0] == {"$eq": [{"$type": "$$failure.occurred_at"}, "date"]}
        assert window_cond[1] == {
            "$gte": ["$$failure.occurred_at", fixed_now - timedelta(days=7)]
        }
        assert window_cond[2] == {"$lte": ["$$failure.occurred_at", fixed_now]}

    @pytest.mark.asyncio
    async def test_maintain_torrent_health_is_idempotent_without_new_events(
        self, items_repository: ItemsRepository, collection_mock
    ):
        collection_mock.update_many = mock.AsyncMock()
        fixed_now = datetime(2026, 9, 7, 12, 0, 0)

        with mock.patch.object(ItemsRepository, "_utc_now", return_value=fixed_now):
            await items_repository.maintain_torrent_health("magnet-uri")
            await items_repository.maintain_torrent_health("magnet-uri")

        assert collection_mock.update_many.await_count == 2
        first_pipeline = collection_mock.update_many.await_args_list[0].args[1]
        second_pipeline = collection_mock.update_many.await_args_list[1].args[1]
        assert first_pipeline == second_pipeline

    @pytest.mark.asyncio
    async def test_appends_failure_and_recomputes_health(
        self, items_repository: ItemsRepository, collection_mock
    ):
        collection_mock.update_many = mock.AsyncMock()
        failure: TorrentFailure = {
            "occurred_at": datetime.now(),
            "failure_point": "update_item_torrent_info",
        }

        await items_repository.record_torrent_failure("magnet-uri", failure)

        collection_mock.update_many.assert_awaited_once()
        query, pipeline = collection_mock.update_many.call_args.args
        assert query == {"magnet_uri": "magnet-uri"}
        assert pipeline[0]["$set"]["torrent_failure_history"]["$filter"]["input"][
            "$concatArrays"
        ]
        assert pipeline[1]["$set"]["torrent_failure_days"]["$size"]
        assert pipeline[2]["$set"]["torrent_is_dying"] == {
            "$gte": ["$torrent_failure_days", 1]
        }

    @pytest.mark.asyncio
    async def test_invalid_timestamp_is_not_appended_and_logs_warning(
        self, items_repository: ItemsRepository, collection_mock
    ):
        collection_mock.update_many = mock.AsyncMock()
        failure = cast(
            TorrentFailure,
            {
                "occurred_at": "invalid",  # type: ignore[typeddict-item]
                "failure_point": "update_item_torrent_info",
            },
        )

        with mock.patch("betor.repositories.items_repository.logger.warning") as warning:
            await items_repository.record_torrent_failure("magnet-uri", failure)

        warning.assert_called_once()
        _, pipeline = collection_mock.update_many.call_args.args
        history_input = pipeline[0]["$set"]["torrent_failure_history"]["$filter"]["input"]
        assert history_input == {"$ifNull": ["$torrent_failure_history", []]}

    @pytest.mark.asyncio
    async def test_future_timestamp_is_not_appended_and_logs_warning(
        self, items_repository: ItemsRepository, collection_mock
    ):
        collection_mock.update_many = mock.AsyncMock()
        fixed_now = datetime(2026, 9, 7, 12, 0, 0)
        failure: TorrentFailure = {
            "occurred_at": fixed_now + timedelta(minutes=1),
            "failure_point": "update_item_torrent_trackers_info",
        }

        with (
            mock.patch.object(ItemsRepository, "_utc_now", return_value=fixed_now),
            mock.patch("betor.repositories.items_repository.logger.warning") as warning,
        ):
            await items_repository.record_torrent_failure("magnet-uri", failure)

        warning.assert_called_once()
        _, pipeline = collection_mock.update_many.call_args.args
        history_input = pipeline[0]["$set"]["torrent_failure_history"]["$filter"]["input"]
        assert history_input == {"$ifNull": ["$torrent_failure_history", []]}

    def test_parse_result_uses_legacy_health_defaults(self):
        result = ItemsRepository.parse_result(
            {
                "_id": "1234",
                "provider_slug": "slug",
                "provider_url": "url",
                "magnet_uri": "magnet",
                "magnet_xt": "xt",
            }
        )

        assert result["torrent_failure_history"] == []
        assert result["torrent_failure_days"] == 0
        assert result["torrent_is_dying"] is False
        assert result["torrent_is_dead"] is False
