from typing import Generator, List
from unittest import mock

import pytest
from faker import Faker

from betor.external_apis import (
    IMDbSuggestionAPI,
    IMDbSuggestionAPIError,
    TMDBTrendingAPI,
    TMDBTrendingAPIError,
)
from betor.services import DeterminesIMDbTMDBIdsService
from betor.types import ItemType, RawItem


@pytest.fixture
def determines_imdb_tmdb_ids_service() -> Generator[DeterminesIMDbTMDBIdsService]:
    with (
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.IMDbSuggestionAPI",
            new_callable=mock.MagicMock,
            spec=IMDbSuggestionAPI,
        ),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.TMDBTrendingAPI",
            new_callable=mock.MagicMock,
            spec=TMDBTrendingAPI,
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
        determines_imdb_tmdb_ids_service.imdb_suggestion_api.execute.side_effect = [
            {
                "d": [
                    {},
                    {"qid": "movie", "id": imdb_id, "l": "Foo Bar"},
                    {"qid": "tvSeries", "id": fake.numerify("tt########"), "l": "Foo"},
                ]
            },
            IMDbSuggestionAPIError,
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
                mock.ANY,
                ItemType.tv,
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
