from collections import OrderedDict
from typing import Generator
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.repositories import ItemsRepository
from betor.types import Item


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
        with mock.patch.object(ItemsRepository, "build_item_data", return_value={}):
            assert ItemsRepository.calculate_hash(mock.MagicMock(spec=Item)) == 53616175


class TestBuildItemData:
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
    def test_ok(self, item, expected):
        assert ItemsRepository.build_item_data(item) == OrderedDict(expected)


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
            }
        )
        result = await items_repository.get("slug", "http://example.com")
        assert result
        assert result["id"] == "1234"

    @pytest.mark.asyncio
    async def test_not_found(
        self,
        items_repository: ItemsRepository,
        collection_mock,
    ):
        collection_mock.find_one = mock.AsyncMock(return_value=None)
        assert await items_repository.get("slug", "http://example.com") is None


class TestInsertOrUpdateItem:
    @pytest.mark.asyncio
    async def test_inserted_ok(self, items_repository: ItemsRepository):
        with (
            mock.patch.object(
                items_repository, "get", new_callable=mock.AsyncMock, return_value=None
            ),
            mock.patch.object(
                items_repository, "insert_item", new_callable=mock.AsyncMock
            ) as insert_item_mock,
        ):
            result = await items_repository.insert_or_update_item(
                mock.MagicMock(spec=Item)
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
                items_repository, "update_item", new_callable=mock.AsyncMock
            ) as update_item_mock,
        ):
            result = await items_repository.insert_or_update_item(
                mock.MagicMock(spec=Item)
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
            result = await items_repository.insert_or_update_item(
                mock.MagicMock(spec=Item)
            )
            assert result == "no_change"
