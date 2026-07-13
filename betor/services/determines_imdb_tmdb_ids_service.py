import logging
from typing import Optional, Tuple

import motor.motor_asyncio

from betor.adapters.determines_strategies import (
    ImdbFindByTmdbStrategy,
    ImdbSearchStrategy,
    ImdbSuggestionStrategy,
    ProviderURLMappingStrategy,
    RawImdbIdStrategy,
    TmdbFindByImdbStrategy,
    TmdbTranslatedTitleSearchStrategy,
    TmdbTrendingStrategy,
)
from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import (
    IMDBIAmIdiotAreYouTooSearchAPI,
    IMDbSuggestionAPI,
    TMDBExternalIdsAPI,
    TMDBFindByIdAPI,
    TMDBSearchMultiAPI,
    TMDBTrendingAPI,
)
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.types import ScoreKey, Scores, StrategyGenerator

logger = logging.getLogger(__name__)


class DeterminesIMDbTMDBIdsService:
    @classmethod
    def best_scored_key(cls, scores: Scores) -> Tuple[ScoreKey, float]:
        if not scores:
            raise ValueError()
        return max(scores.items(), key=lambda kv: kv[1])

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.tmdb_trending_api = TMDBTrendingAPI()
        self.tmdb_find_by_id_api = TMDBFindByIdAPI()
        self.imdb_suggestion_api = IMDbSuggestionAPI()
        self.provider_url_imdb_mapping_repository = ProviderURLIMDBMappingRepository(
            mongodb_client
        )
        self.tmdb_external_ids_api = TMDBExternalIdsAPI()
        self.imdb_search_api = IMDBIAmIdiotAreYouTooSearchAPI()
        self.tmdb_search_multi_api = TMDBSearchMultiAPI()
        self.strategies = [
            ProviderURLMappingStrategy(
                self.provider_url_imdb_mapping_repository, self.tmdb_find_by_id_api
            ),
            RawImdbIdStrategy(),
            ImdbSearchStrategy(self.imdb_search_api),
            ImdbSuggestionStrategy(self.imdb_suggestion_api),
            TmdbTrendingStrategy(self.tmdb_trending_api),
            TmdbTranslatedTitleSearchStrategy(self.tmdb_search_multi_api),
            TmdbFindByImdbStrategy(self.tmdb_find_by_id_api),
            ImdbFindByTmdbStrategy(self.tmdb_external_ids_api),
        ]

    async def determines(self, raw_item: RawItem) -> Tuple[
        Optional[str],
        Optional[float],
        Optional[str],
        Optional[float],
        Optional[ItemType],
    ]:
        imdb_scores: Scores = {}
        tmdb_scores: Scores = {}

        async for strategy, score, ii, ti, it in self.run_strategies(
            raw_item, imdb_scores, tmdb_scores
        ):
            logger.debug(
                f"Strategy {strategy.__class__.__name__} returned score {score} for item_type {it} with imdb_id {ii} and tmdb_id {ti}"
            )
            if ii:
                key = (
                    ii,
                    it,
                )
                imdb_scores[key] = imdb_scores.get(key, 0.0) + score
            if ti:
                key = (
                    ti,
                    it,
                )
                tmdb_scores[key] = tmdb_scores.get(key, 0.0) + score

        imdb_id: Optional[str]
        imdb_score_value: Optional[float]
        imdb_item_type: Optional[ItemType]
        try:
            imdb_score, imdb_score_value = self.best_scored_key(imdb_scores)
            imdb_id, imdb_item_type = imdb_score
        except ValueError:
            imdb_id, imdb_score_value, imdb_item_type = None, None, None

        tmdb_id: Optional[str]
        tmdb_score_value: Optional[float]
        tmdb_item_type: Optional[ItemType]
        try:
            tmdb_score, tmdb_score_value = self.best_scored_key(tmdb_scores)
            tmdb_id, tmdb_item_type = tmdb_score
        except ValueError:
            tmdb_id, tmdb_score_value, tmdb_item_type = None, None, None

        item_type = imdb_item_type or tmdb_item_type
        return imdb_id, imdb_score_value, tmdb_id, tmdb_score_value, item_type

    async def run_strategies(
        self, raw_item: RawItem, imdb_scores: Scores, tmdb_scores: Scores
    ) -> StrategyGenerator:
        for strategy in self.strategies:
            async for result in strategy(
                raw_item, imdb_scores=imdb_scores, tmdb_scores=tmdb_scores
            ):
                yield result
