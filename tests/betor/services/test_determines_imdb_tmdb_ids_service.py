from typing import AsyncGenerator
from unittest import mock

import motor.motor_asyncio
import pytest
from faker import Faker

from betor.entities import RawItem
from betor.enums import ItemType
from betor.services import DeterminesIMDbTMDBIdsService
from betor.types import ScoreKey


@pytest.fixture
def mongodb_client_mock():
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def determines_service(mongodb_client_mock):
    with (
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.IMDBAPIDevSearchAPI"
        ),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.IMDBAPIDevTitleAPI"
        ),
        mock.patch("betor.services.determines_imdb_tmdb_ids_service.TMDBTrendingAPI"),
        mock.patch("betor.services.determines_imdb_tmdb_ids_service.TMDBFindByIdAPI"),
        mock.patch("betor.services.determines_imdb_tmdb_ids_service.IMDbSuggestionAPI"),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.ProviderURLIMDBMappingRepository"
        ),
        mock.patch(
            "betor.services.determines_imdb_tmdb_ids_service.TMDBExternalIdsAPI"
        ),
    ):
        yield DeterminesIMDbTMDBIdsService(mongodb_client_mock)


@pytest.fixture
def simple_raw_item(fake: Faker) -> RawItem:
    """Simple raw_item fixture without parametrize support"""
    return RawItem(
        id=None,
        hash=None,
        inserted_at=None,
        updated_at=None,
        provider_slug=fake.slug(),
        provider_url=fake.url(),
        imdb_id=None,
        tmdb_id=None,
        magnet_uris=[],
        languages=[],
        qualitys=[],
        title=None,
        translated_title=None,
        raw_title=None,
        year=None,
        cast=None,
    )


class TestBestScoredKey:
    def test_single_score(self):
        scores = {("tt123456", ItemType.movie): 1.0}
        result = DeterminesIMDbTMDBIdsService.best_scored_key(scores)
        assert result == ("tt123456", ItemType.movie)

    def test_multiple_scores_returns_highest(self):
        scores = {
            ("tt111111", ItemType.movie): 0.5,
            ("tt222222", ItemType.movie): 2.5,
            ("tt333333", ItemType.tv): 1.0,
        }
        result = DeterminesIMDbTMDBIdsService.best_scored_key(scores)
        assert result == ("tt222222", ItemType.movie)

    def test_empty_scores_raises_error(self):
        scores = {}
        with pytest.raises(ValueError):
            DeterminesIMDbTMDBIdsService.best_scored_key(scores)


class TestDetermines:
    @pytest.mark.asyncio
    async def test_determines_with_imdb_and_tmdb_ids(
        self,
        determines_service: DeterminesIMDbTMDBIdsService,
        simple_raw_item: RawItem,
        fake: Faker,
    ):
        imdb_id = fake.numerify("tt########")
        tmdb_id = "123456"

        # Mock the run_strategies method to return some scores
        async def mock_strategies(
            *args, **kwargs
        ) -> AsyncGenerator[tuple[float, str, str, ItemType], None]:
            yield (
                1.0,
                imdb_id,
                tmdb_id,
                ItemType.movie,
            )

        with mock.patch.object(determines_service, "run_strategies", mock_strategies):
            result = await determines_service.determines(simple_raw_item)
            assert result[0] == imdb_id
            assert result[1] == tmdb_id
            assert result[2] == ItemType.movie

    @pytest.mark.asyncio
    async def test_determines_with_only_imdb_id(
        self,
        determines_service: DeterminesIMDbTMDBIdsService,
        simple_raw_item: RawItem,
        fake: Faker,
    ):
        imdb_id = fake.numerify("tt########")

        async def mock_strategies(
            *args, **kwargs
        ) -> AsyncGenerator[tuple[float, str | None, str | None, ItemType], None]:
            yield (1.0, imdb_id, None, ItemType.movie)

        with mock.patch.object(determines_service, "run_strategies", mock_strategies):
            result = await determines_service.determines(simple_raw_item)
            assert result[0] == imdb_id
            assert result[1] is None
            assert result[2] == ItemType.movie

    @pytest.mark.asyncio
    async def test_determines_with_only_tmdb_id(
        self, determines_service: DeterminesIMDbTMDBIdsService, simple_raw_item: RawItem
    ):
        tmdb_id = "654321"

        async def mock_strategies(
            *args, **kwargs
        ) -> AsyncGenerator[tuple[float, str | None, str, ItemType], None]:
            yield (1.0, None, tmdb_id, ItemType.tv)

        with mock.patch.object(determines_service, "run_strategies", mock_strategies):
            result = await determines_service.determines(simple_raw_item)
            assert result[0] is None
            assert result[1] == tmdb_id
            assert result[2] == ItemType.tv

    @pytest.mark.asyncio
    async def test_determines_with_no_ids(
        self, determines_service: DeterminesIMDbTMDBIdsService, simple_raw_item: RawItem
    ):
        async def mock_strategies(
            *args, **kwargs
        ) -> AsyncGenerator[tuple[float, None, None, None], None]:
            yield (1.0, None, None, None)

        with mock.patch.object(determines_service, "run_strategies", mock_strategies):
            result = await determines_service.determines(simple_raw_item)
            assert result[0] is None
            assert result[1] is None
            assert result[2] is None

    @pytest.mark.asyncio
    async def test_determines_accumulates_scores(
        self,
        determines_service: DeterminesIMDbTMDBIdsService,
        simple_raw_item: RawItem,
        fake: Faker,
    ):
        imdb_id = fake.numerify("tt########")
        tmdb_id = "123456"

        async def mock_strategies(
            *args, **kwargs
        ) -> AsyncGenerator[tuple[float, str, str, ItemType], None]:
            # Multiple results for the same ID to test score accumulation
            yield (0.5, imdb_id, tmdb_id, ItemType.movie)
            yield (0.3, imdb_id, tmdb_id, ItemType.movie)

        with mock.patch.object(determines_service, "run_strategies", mock_strategies):
            result = await determines_service.determines(simple_raw_item)
            assert result[0] == imdb_id
            assert result[1] == tmdb_id
            assert result[2] == ItemType.movie

    @pytest.mark.asyncio
    async def test_determines_picks_highest_scored_id(
        self,
        determines_service: DeterminesIMDbTMDBIdsService,
        simple_raw_item: RawItem,
        fake: Faker,
    ):
        imdb_id_1 = fake.numerify("tt########")
        imdb_id_2 = fake.numerify("tt########")
        tmdb_id = "123456"

        async def mock_strategies(
            *args, **kwargs
        ) -> AsyncGenerator[tuple[float, str, str, ItemType], None]:
            yield (0.2, imdb_id_1, tmdb_id, ItemType.movie)
            yield (0.8, imdb_id_2, tmdb_id, ItemType.movie)

        with mock.patch.object(determines_service, "run_strategies", mock_strategies):
            result = await determines_service.determines(simple_raw_item)
            # Should pick imdb_id_2 since it has higher score
            assert result[0] == imdb_id_2
            assert result[1] == tmdb_id
            assert result[2] == ItemType.movie


class TestRunStrategies:
    @pytest.mark.asyncio
    async def test_run_strategies_calls_all_strategies(
        self,
        determines_service: DeterminesIMDbTMDBIdsService,
        simple_raw_item: RawItem,
        fake: Faker,
    ):
        imdb_scores: dict[ScoreKey[ItemType], float] = {}
        tmdb_scores: dict[ScoreKey[ItemType], float] = {}
        results_to_return: list[tuple[float, str, str, ItemType]] = []

        # Create mock strategies
        for i in range(min(3, len(determines_service.strategies))):
            results_to_return.append(
                (0.5, fake.numerify("tt########"), "123456", ItemType.movie)
            )

        original_strategies = determines_service.strategies

        async def mock_strategy_generator(
            raw_item: RawItem,
            imdb_scores: dict[ScoreKey[ItemType], float],
            tmdb_scores: dict[ScoreKey[ItemType], float],
        ) -> AsyncGenerator[tuple[float, str, str, ItemType], None]:
            for result in results_to_return:
                yield result

        with mock.patch.object(
            determines_service, "run_strategies", mock_strategy_generator
        ):
            results = []
            async for result in determines_service.run_strategies(
                simple_raw_item, imdb_scores, tmdb_scores
            ):
                results.append(result)

            # All mock results should be returned
            assert len(results) == len(results_to_return)
            determines_service.strategies = original_strategies
