from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import IMDBAPIDevSearchAPI, IMDBAPIDevSearchAPIError
from betor.types import Scores, StrategyGenerator
from betor.utils import jaccard_similarity

from .strategy import Strategy


class ImdbSearchStrategy(Strategy):
    def __init__(self, imdb_search_api: IMDBAPIDevSearchAPI):
        self.imdb_search_api = imdb_search_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        for query in Strategy.build_queries(raw_item):
            try:
                data = await self.imdb_search_api.execute(query)
            except IMDBAPIDevSearchAPIError:
                continue
            for title in data.get("titles", []):
                similarity = jaccard_similarity(
                    title.get("primaryTitle", ""),
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                if title.get("type") == "movie":
                    yield similarity * 50, title.get("id"), None, ItemType.movie
                if title.get("type") in ["tvSeries", "tvMiniSeries"]:
                    yield similarity * 50, title.get("id"), None, ItemType.tv
                similarity = jaccard_similarity(
                    title.get("originalTitle", ""),
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                if title.get("type") == "movie":
                    yield similarity * 50, title.get("id"), None, ItemType.movie
                if title.get("type") in ["tvSeries", "tvMiniSeries"]:
                    yield similarity * 50, title.get("id"), None, ItemType.tv
