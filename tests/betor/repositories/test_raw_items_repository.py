from collections import OrderedDict
from typing import Generator
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import RawItem
from betor.repositories import RawItemsRepository


@pytest.fixture()
def mongodb_client_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture()
def collection_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorCollection)


@pytest.fixture()
def raw_items_repository(
    mongodb_client_mock, collection_mock
) -> Generator[RawItemsRepository]:
    with mock.patch.object(
        RawItemsRepository,
        "collection",
        new_callable=mock.PropertyMock,
        return_value=collection_mock,
    ):
        yield RawItemsRepository(mongodb_client_mock)


class TestCalculateHash:
    def test_ok(self):
        with mock.patch.object(RawItemsRepository, "build_data", return_value={}):
            assert (
                RawItemsRepository.calculate_hash(mock.MagicMock(spec=RawItem))
                == 53616175
            )


class TestBuildData:
    @pytest.mark.parametrize(
        (
            "raw_item",
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
                        "languages",
                        ["pt"],
                    ),
                    (
                        "provider_slug",
                        "slug",
                    ),
                ],
            ),
        ],
    )
    def test_ok(self, raw_item, expected):
        assert RawItemsRepository.build_data(raw_item) == OrderedDict(expected)


class TestGet:
    @pytest.mark.asyncio
    async def test_ok(
        self,
        raw_items_repository: RawItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(
            return_value={
                "_id": "1234",
                "provider_slug": "slug",
                "provider_url": "http://example.com",
            }
        )
        result = await raw_items_repository.get("slug", "http://example.com")
        assert result
        assert result["id"] == "1234"

    @pytest.mark.asyncio
    async def test_not_found(
        self,
        raw_items_repository: RawItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(return_value=None)
        assert await raw_items_repository.get("slug", "http://example.com") is None


class TestGetByProviderUrl:
    @pytest.mark.asyncio
    async def test_ok(
        self,
        raw_items_repository: RawItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(
            return_value={
                "_id": "1234",
                "provider_slug": "slug",
                "provider_url": "http://example.com",
            }
        )
        result = await raw_items_repository.get_by_provider_url("http://example.com")
        assert result
        assert result["id"] == "1234"

    @pytest.mark.asyncio
    async def test_not_found(
        self,
        raw_items_repository: RawItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(return_value=None)
        assert (
            await raw_items_repository.get_by_provider_url("http://example.com") is None
        )


class TestInsertOrUpdateItem:
    @pytest.mark.asyncio
    async def test_inserted_ok(self, raw_items_repository: RawItemsRepository):
        with (
            mock.patch.object(
                raw_items_repository,
                "get",
                new_callable=mock.AsyncMock,
                return_value=None,
            ),
            mock.patch.object(
                raw_items_repository, "insert", new_callable=mock.AsyncMock
            ) as insert_item_mock,
        ):
            result = await raw_items_repository.insert_or_update(
                mock.MagicMock(spec=RawItem)
            )
            assert result == "inserted"
            insert_item_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_updated_ok(self, raw_items_repository: RawItemsRepository):
        with (
            mock.patch.object(
                raw_items_repository,
                "get",
                new_callable=mock.AsyncMock,
                return_value={"hash": "123"},
            ),
            mock.patch(
                "betor.repositories.raw_items_repository.RawItemsRepository.calculate_hash",
                return_value="321",
            ),
            mock.patch.object(
                raw_items_repository, "update", new_callable=mock.AsyncMock
            ) as update_item_mock,
        ):
            result = await raw_items_repository.insert_or_update(
                mock.MagicMock(spec=RawItem)
            )
            assert result == "updated"
            update_item_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_change_ok(self, raw_items_repository: RawItemsRepository):
        with (
            mock.patch.object(
                raw_items_repository,
                "get",
                new_callable=mock.AsyncMock,
                return_value={"hash": "123"},
            ),
            mock.patch(
                "betor.repositories.raw_items_repository.RawItemsRepository.calculate_hash",
                return_value="123",
            ),
        ):
            result = await raw_items_repository.insert_or_update(
                mock.MagicMock(spec=RawItem)
            )
            assert result == "no_change"
