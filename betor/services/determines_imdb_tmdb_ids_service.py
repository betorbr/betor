from typing import Optional, Tuple

import motor.motor_asyncio

from betor.adapters.determines_strategies import (
    ImdbFindByTmdbStrategy,
    ImdbSearchStrategy,
    ImdbSuggestionStrategy,
    ProviderURLMappingStrategy,
    RawImdbIdStrategy,
    TmdbFindByImdbStrategy,
    TmdbTrendingStrategy,
)
from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import (
    IMDBAPIDevSearchAPI,
    IMDBAPIDevTitleAPI,
    IMDbSuggestionAPI,
    TMDBExternalIdsAPI,
    TMDBFindByIdAPI,
    TMDBTrendingAPI,
)
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.types import ScoreKey, Scores, StrategyGenerator


class DeterminesIMDbTMDBIdsService:
    @classmethod
    def best_scored_key(cls, scores: Scores) -> ScoreKey[ItemType]:
        if not scores:
            raise ValueError()
        return max(scores.items(), key=lambda kv: kv[1])[0]

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.imdb_api_dev_search_api = IMDBAPIDevSearchAPI()
        self.imdb_api_dev_title_api = IMDBAPIDevTitleAPI()
        self.tmdb_trending_api = TMDBTrendingAPI()
        self.tmdb_find_by_id_api = TMDBFindByIdAPI()
        self.imdb_suggestion_api = IMDbSuggestionAPI()
        self.provider_url_imdb_mapping_repository = ProviderURLIMDBMappingRepository(
            mongodb_client
        )
        self.tmdb_external_ids_api = TMDBExternalIdsAPI()
        self.strategies = [
            ProviderURLMappingStrategy(
                self.provider_url_imdb_mapping_repository, self.imdb_api_dev_title_api
            ),
            RawImdbIdStrategy(self.imdb_api_dev_title_api),
            ImdbSuggestionStrategy(self.imdb_suggestion_api),
            ImdbSearchStrategy(self.imdb_api_dev_search_api),
            TmdbTrendingStrategy(self.tmdb_trending_api),
            TmdbFindByImdbStrategy(self.tmdb_find_by_id_api),
            ImdbFindByTmdbStrategy(self.tmdb_external_ids_api),
        ]

    async def determines(
        self, raw_item: RawItem
    ) -> Tuple[Optional[str], Optional[str], Optional[ItemType]]:
        imdb_scores: Scores = {}
        tmdb_scores: Scores = {}

        async for score, ii, ti, item_type in self.run_strategies(
            raw_item, imdb_scores, tmdb_scores
        ):
            if ii:
                key = (ii, item_type)
                imdb_scores[key] = imdb_scores.get(key, 0.0) + score
            if ti:
                key = (ti, item_type)
                tmdb_scores[key] = tmdb_scores.get(key, 0.0) + score

        imdb_id: Optional[str]
        imdb_item_type: Optional[ItemType]
        try:
            imdb_id, imdb_item_type = self.best_scored_key(imdb_scores)
        except ValueError:
            imdb_id, imdb_item_type = None, None

        tmdb_id: Optional[str]
        tmdb_item_type: Optional[ItemType]
        try:
            tmdb_id, tmdb_item_type = self.best_scored_key(tmdb_scores)
        except ValueError:
            tmdb_id, tmdb_item_type = None, None

        item_type = imdb_item_type or tmdb_item_type
        return imdb_id, tmdb_id, item_type

    async def run_strategies(
        self, raw_item: RawItem, imdb_scores: Scores, tmdb_scores: Scores
    ) -> StrategyGenerator[ItemType]:
        for strategy in self.strategies:
            async for result in strategy(
                raw_item, imdb_scores=imdb_scores, tmdb_scores=tmdb_scores
            ):
                yield result
