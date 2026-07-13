from typing import Generator, Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBTrendingAPI, TMDBTrendingAPIError
from betor.types import Scores, StrategyGenerator
from betor.utils import jaccard_similarity

from .strategy import Strategy


class TmdbTrendingStrategy(Strategy):
    @staticmethod
    def build_queries(raw_item: RawItem) -> Generator[str, None, None]:
        if raw_item["title"] and raw_item["year"]:
            yield f"{raw_item['title']} {raw_item['year']}"
        if raw_item["translated_title"] and raw_item["year"]:
            yield f"{raw_item['translated_title']} {raw_item['year']}"
        if raw_item["title"]:
            yield raw_item["title"]
            if "/" in raw_item["title"]:
                yield from map(lambda v: v.strip(), raw_item["title"].split("/"))
        if raw_item["translated_title"]:
            yield raw_item["translated_title"]

    def __init__(self, tmdb_trending_api: TMDBTrendingAPI):
        self.tmdb_trending_api = tmdb_trending_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        for query in TmdbTrendingStrategy.build_queries(raw_item):
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
                if similarity < 0.95:
                    continue
                if result.get("media_type") == "movie":
                    yield self, similarity * 100, None, str(
                        result.get("id")
                    ), ItemType.movie
                if result.get("media_type") == "tv":
                    yield self, similarity * 100, None, str(
                        result.get("id")
                    ), ItemType.tv
