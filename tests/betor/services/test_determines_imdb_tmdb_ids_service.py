from typing import Generator, List
from unittest import mock

import pytest
from faker import Faker

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import (
    IMDBAPIDevSearchAPI,
    IMDBAPIDevSearchAPIError,
    IMDBAPIDevTitleAPI,
    TMDBFindByIdAPI,
    TMDBFindByIdResponse,
    TMDBFindByIdResponseResult,
    TMDBTrendingAPI,
    TMDBTrendingAPIError,
)
from betor.services import DeterminesIMDbTMDBIdsService


@pytest.fixture
def determines_imdb_tmdb_ids_service() -> Generator[DeterminesIMDbTMDBIdsService]:
    with (
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.IMDBAPIDevSearchAPI",
            new_callable=mock.MagicMock,
            spec=IMDBAPIDevSearchAPI,
        ),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.IMDBAPIDevTitleAPI",
            new_callable=mock.MagicMock,
            spec=IMDBAPIDevTitleAPI,
        ),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.TMDBTrendingAPI",
            new_callable=mock.MagicMock,
            spec=TMDBTrendingAPI,
        ),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.TMDBFindByIdAPI",
            new_callable=mock.MagicMock,
            spec=TMDBFindByIdAPI,
        ),
    ):
        yield DeterminesIMDbTMDBIdsService()


class TestBuildQuerys:
    @pytest.mark.parametrize(
        (
            "raw_item",
            "expected",
        ),
        [
            (
                {},
                [],
            ),
            (
                {"title": "foo"},
                ["foo"],
            ),
            (
                {
                    "title": "foo",
                    "translated_title": "bar",
                    "year": 2025,
                },
                ["foo 2025", "bar 2025", "foo", "bar"],
            ),
            (
                {"title": "foo / bar"},
                ["foo / bar", "foo", "bar"],
            ),
        ],
        indirect=["raw_item"],
    )
    def test_ok(self, raw_item: RawItem, expected: List[str]):
        assert list(DeterminesIMDbTMDBIdsService.build_querys(raw_item)) == expected


class TestBestDeterminesOption:
    @pytest.mark.asyncio
    async def test_ok(self):
        determines_generator = mock.MagicMock()
        determines_generator.__aiter__.return_value = [
            (
                0.5,
                "1234",
                "5678",
            ),
            (
                1.0,
                "9012",
                "3456",
            ),
            (
                0.75,
                "7890",
                "1234",
            ),
        ]
        assert await DeterminesIMDbTMDBIdsService.best_determines_option(
            determines_generator
        ) == (
            "9012",
            "3456",
        )

    @pytest.mark.asyncio
    async def test_empty(self):
        determines_generator = mock.AsyncMock()
        assert await DeterminesIMDbTMDBIdsService.best_determines_option(
            determines_generator
        ) == (
            None,
            None,
        )


class TestDetermines:
    @pytest.mark.asyncio
    async def test_ok(
        self, determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService
    ):
        with (
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.best_determines_option",
                new_callable=mock.AsyncMock,
                side_effect=[
                    ("1234", ItemType.movie),
                    ("5678", ItemType.movie),
                ],
            ),
            mock.patch.object(determines_imdb_tmdb_ids_service, "determines_imdb_id"),
            mock.patch.object(determines_imdb_tmdb_ids_service, "determines_tmdb_id"),
        ):
            raw_item = mock.MagicMock(spec=RawItem)
            assert await determines_imdb_tmdb_ids_service.determines(raw_item) == (
                "1234",
                "5678",
                ItemType.movie,
            )


class TestDeterminesImdbId:
    @pytest.mark.parametrize("raw_item", [{"title": "Foo Bar"}], indirect=["raw_item"])
    @pytest.mark.asyncio
    async def test_ok(
        self,
        raw_item: RawItem,
        fake: Faker,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
    ):
        imdb_id = fake.numerify("tt########")
        determines_imdb_tmdb_ids_service.imdb_api_dev_search_api.execute.side_effect = [
            {
                "titles": [
                    {
                        "type": "movie",
                        "id": imdb_id,
                        "originalTitle": "Foo Bar",
                        "primaryTitle": "Foo Bar",
                    },
                    {
                        "type": "tvSeries",
                        "id": fake.numerify("tt########"),
                        "originalTitle": "Foo",
                        "primaryTitle": "Foo",
                    },
                ]
            },
            IMDBAPIDevSearchAPIError,
        ]
        with (
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.build_querys",
                return_value=["foo 2025", "foo"],
            ),
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.jaccard_similarity",
                return_value=1.0,
            ),
        ):
            result = [
                item
                async for item in determines_imdb_tmdb_ids_service.determines_imdb_id(
                    raw_item
                )
            ]
            assert result[0] == (
                1.0,
                imdb_id,
                ItemType.movie,
            )
            assert result[1] == (
                1.0,
                imdb_id,
                ItemType.movie,
            )
            assert result[2] == (
                1.0,
                mock.ANY,
                ItemType.tv,
            )
            assert result[3] == (
                1.0,
                mock.ANY,
                ItemType.tv,
            )

    @pytest.mark.parametrize(
        "raw_item",
        [{"title": "Foo Bar", "imdb_id": "tt12345678"}],
        indirect=["raw_item"],
    )
    @pytest.mark.asyncio
    async def test_with_imdb_id_ok(
        self,
        raw_item: RawItem,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
    ):
        imdb_id = "tt12345678"
        determines_imdb_tmdb_ids_service.imdb_api_dev_title_api.execute.return_value = {
            "type": "movie",
            "id": imdb_id,
        }
        result = [
            item
            async for item in determines_imdb_tmdb_ids_service.determines_imdb_id(
                raw_item
            )
        ]
        assert result[0] == (
            1.0,
            imdb_id,
            ItemType.movie,
        )


class TestDeterminesTmdbId:
    @pytest.mark.parametrize("raw_item", [{"title": "Foo Bar"}], indirect=["raw_item"])
    @pytest.mark.asyncio
    async def test_ok(
        self,
        raw_item: RawItem,
        fake: Faker,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
    ):
        tmdb_id = fake.pyint(1000000, 9999999)
        determines_imdb_tmdb_ids_service.tmdb_trending_api.execute.side_effect = [
            TMDBTrendingAPIError,
            {
                "results": [
                    {"id": tmdb_id, "name": "Foo Bar", "media_type": "movie"},
                    {
                        "id": fake.pyint(1000000, 9999999),
                        "name": "Foo",
                        "media_type": "tv",
                    },
                    "---",
                ]
            },
        ]
        with (
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.build_querys",
                return_value=["foo 2025", "foo"],
            ),
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.jaccard_similarity",
                return_value=1.0,
            ),
        ):
            result = [
                item
                async for item in determines_imdb_tmdb_ids_service.determines_tmdb_id(
                    raw_item
                )
            ]
            assert len(result) == 2
            assert result[0] == (
                1.0,
                str(tmdb_id),
                ItemType.movie,
            )
            assert result[1] == (
                1.0,
                mock.ANY,
                ItemType.tv,
            )

    @pytest.mark.parametrize("raw_item", [{"title": "Foo Bar"}], indirect=["raw_item"])
    @pytest.mark.asyncio
    async def test_force_item_type(
        self,
        raw_item: RawItem,
        fake: Faker,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
    ):
        tmdb_id = fake.pyint(1000000, 9999999)
        determines_imdb_tmdb_ids_service.tmdb_trending_api.execute.side_effect = [
            TMDBTrendingAPIError,
            {
                "results": [
                    {
                        "id": fake.pyint(1000000, 9999999),
                        "name": "Foo Bar",
                        "media_type": "movie",
                    },
                    {
                        "id": tmdb_id,
                        "name": "Foo",
                        "media_type": "tv",
                    },
                    "---",
                ]
            },
        ]
        with (
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.build_querys",
                return_value=["foo 2025", "foo"],
            ),
            mock.patch(
                "betor.services.determines_imdb_tmdb_ids_service.jaccard_similarity",
                return_value=1.0,
            ),
        ):
            result = [
                item
                async for item in determines_imdb_tmdb_ids_service.determines_tmdb_id(
                    raw_item, ItemType.tv
                )
            ]
            assert len(result) == 1
            assert result[0] == (
                1.0,
                str(tmdb_id),
                ItemType.tv,
            )

    @mock.patch(
        "betor.services.determines_imdb_tmdb_ids_service.tmdb_api_settings.access_token",
        return_value="123",
    )
    @pytest.mark.asyncio
    async def test_imdb_id_with_tmdb_access_token_empty_result(
        self,
        raw_item: RawItem,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
        *mocks,
    ):
        determines_imdb_tmdb_ids_service.tmdb_find_by_id_api.execute.side_effect = [
            TMDBFindByIdResponse(movie_results=[], tv_results=[])
        ]
        with mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.build_querys",
            return_value=[],
        ) as build_querys_mock:
            result = [
                item
                async for item in determines_imdb_tmdb_ids_service.determines_tmdb_id(
                    raw_item, imdb_id="tt12345678"
                )
            ]
            assert len(result) == 0
            build_querys_mock.assert_called_once()

    @mock.patch(
        "betor.services.determines_imdb_tmdb_ids_service.tmdb_api_settings.access_token",
        return_value="123",
    )
    @pytest.mark.asyncio
    async def test_imdb_id_with_tmdb_access_token_ok(
        self,
        raw_item: RawItem,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
        *mocks,
    ):
        determines_imdb_tmdb_ids_service.tmdb_find_by_id_api.execute.side_effect = [
            TMDBFindByIdResponse(
                movie_results=[TMDBFindByIdResponseResult(id=123, media_type="movie")],
                tv_results=[],
            )
        ]
        with mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.build_querys",
            return_value=[],
        ) as build_querys_mock:
            result = [
                item
                async for item in determines_imdb_tmdb_ids_service.determines_tmdb_id(
                    raw_item, imdb_id="tt12345678"
                )
            ]
            assert len(result) == 1
            assert result[0][0] == 1
            assert result[0][1] == "123"
            build_querys_mock.assert_not_called()

    @mock.patch(
        "betor.services.determines_imdb_tmdb_ids_service.tmdb_api_settings.access_token",
        return_value="123",
    )
    @pytest.mark.asyncio
    async def test_imdb_id_with_tmdb_access_token_force_item_type_ok(
        self,
        raw_item: RawItem,
        determines_imdb_tmdb_ids_service: DeterminesIMDbTMDBIdsService,
        *mocks,
    ):
        determines_imdb_tmdb_ids_service.tmdb_find_by_id_api.execute.side_effect = [
            TMDBFindByIdResponse(
                movie_results=[TMDBFindByIdResponseResult(id=123, media_type="movie")],
                tv_results=[TMDBFindByIdResponseResult(id=321, media_type="tv")],
            )
        ]
        with mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.DeterminesIMDbTMDBIdsService.build_querys",
            return_value=[],
        ) as build_querys_mock:
            result = [
                item
                async for item in determines_imdb_tmdb_ids_service.determines_tmdb_id(
                    raw_item, force_item_type=ItemType.tv, imdb_id="tt12345678"
                )
            ]
            assert len(result) == 1
            assert result[0][0] == 1
            assert result[0][1] == "321"
            build_querys_mock.assert_not_called()
