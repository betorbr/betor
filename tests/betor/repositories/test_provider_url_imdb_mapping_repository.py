from typing import Generator
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.enums import ProviderURLIMDBMappingSortEnum
from betor.repositories import ProviderURLIMDBMappingRepository


@pytest.fixture()
def mongodb_client_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture()
def collection_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorCollection)


@pytest.fixture()
def provider_url_imdb_mapping_repository(
    mongodb_client_mock, collection_mock
) -> Generator[ProviderURLIMDBMappingRepository, None, None]:
    with mock.patch.object(
        ProviderURLIMDBMappingRepository,
        "collection",
        new_callable=mock.PropertyMock,
        return_value=collection_mock,
    ):
        yield ProviderURLIMDBMappingRepository(mongodb_client_mock)


class TestParseResults:
    def test_ok(
        self, provider_url_imdb_mapping_repository: ProviderURLIMDBMappingRepository
    ):
        results = [
            {
                "_id": "1234",
                "provider_url": "http://example.com",
                "imdb_id": "tt1234567",
            }
        ]

        parsed = ProviderURLIMDBMappingRepository.parse_results(results)

        assert len(parsed) == 1
        assert parsed[0]["id"] == "1234"
        assert parsed[0]["provider_url"] == "http://example.com"
        assert parsed[0]["imdb_id"] == "tt1234567"


class TestApaginateParams:
    def test_ok(
        self, provider_url_imdb_mapping_repository: ProviderURLIMDBMappingRepository
    ):
        collection, query_filter, cursor_sort, transformer = (
            provider_url_imdb_mapping_repository.apaginate_params(
                ProviderURLIMDBMappingSortEnum.inserted_at_desc,
                provider_url="http://example.com",
            )
        )

        assert collection == provider_url_imdb_mapping_repository.collection
        assert query_filter == {"provider_url": "http://example.com"}
        assert cursor_sort == ("inserted_at", -1)
        assert transformer == ProviderURLIMDBMappingRepository.parse_results


class TestDelete:
    @pytest.mark.asyncio
    async def test_deleted(
        self,
        provider_url_imdb_mapping_repository: ProviderURLIMDBMappingRepository,
        collection_mock,
    ):
        delete_result = mock.MagicMock()
        delete_result.deleted_count = 1
        collection_mock.delete_one = mock.AsyncMock(return_value=delete_result)

        deleted = await provider_url_imdb_mapping_repository.delete(
            "http://example.com"
        )

        assert deleted is True
        collection_mock.delete_one.assert_awaited_once_with(
            {"provider_url": "http://example.com"}
        )

    @pytest.mark.asyncio
    async def test_not_deleted(
        self,
        provider_url_imdb_mapping_repository: ProviderURLIMDBMappingRepository,
        collection_mock,
    ):
        delete_result = mock.MagicMock()
        delete_result.deleted_count = 0
        collection_mock.delete_one = mock.AsyncMock(return_value=delete_result)

        deleted = await provider_url_imdb_mapping_repository.delete(
            "http://example.com"
        )

        assert deleted is False
