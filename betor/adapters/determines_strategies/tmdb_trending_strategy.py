from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBTrendingAPI, TMDBTrendingAPIError
from betor.types import Scores, StrategyGenerator
from betor.utils import jaccard_similarity

from .strategy import Strategy


class TmdbTrendingStrategy(Strategy):
    def __init__(self, tmdb_trending_api: TMDBTrendingAPI):
        self.tmdb_trending_api = tmdb_trending_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        for query in Strategy.build_queries(raw_item):
            try:
                data = await self.tmdb_trending_api.execute(query)
            except TMDBTrendingAPIError:
                continue
            for result in data.get("results", []):
                if isinstance(result, str):
                    continue
                similarity = jaccard_similarity(
                    result.get("name", ""),
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                if result.get("media_type") == "movie":
                    yield similarity * 50, None, str(result.get("id")), ItemType.movie
                if result.get("media_type") == "tv":
                    yield similarity * 50, None, str(result.get("id")), ItemType.tv
