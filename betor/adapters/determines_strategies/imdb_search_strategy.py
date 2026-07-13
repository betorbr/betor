from typing import Generator, Optional

from betor.entities import RawItem
from betor.external_apis import (
    IMDBIAmIdiotAreYouTooSearchAPI,
    IMDBIAmIdiotAreYouTooSearchAPIError,
)
from betor.types import Scores, StrategyGenerator
from betor.utils import jaccard_similarity

from .strategy import Strategy


class ImdbSearchStrategy(Strategy):
    @classmethod
    def build_queries(cls, raw_item: RawItem) -> Generator[str, None, None]:
        if raw_item["title"]:
            yield raw_item["title"]
        if raw_item["translated_title"]:
            yield raw_item["translated_title"]

    def __init__(self, imdb_search_api: IMDBIAmIdiotAreYouTooSearchAPI):
        self.imdb_search_api = imdb_search_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        for query in ImdbSearchStrategy.build_queries(raw_item):
            try:
                data = await self.imdb_search_api.execute(query)
            except IMDBIAmIdiotAreYouTooSearchAPIError:
                continue
            for item in data["description"]:
                similarity = jaccard_similarity(
                    item["#TITLE"],
                    query,
                )
                if similarity < 0.95:
                    continue
                yield self, similarity * 100, item["#IMDB_ID"], None, None
