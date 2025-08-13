from typing import AsyncGenerator, Generator, Optional, Tuple

from betor.external_apis import (
    IMDbSuggestionAPI,
    IMDbSuggestionAPIError,
    TMDBTrendingAPI,
    TMDBTrendingAPIError,
)
from betor.types import ItemType, RawItem
from betor.utils import jaccard_similarity

DeterminesOption = Tuple[float, Optional[str], Optional[ItemType]]
DeterminesGenerator = AsyncGenerator[DeterminesOption]


class DeterminesIMDbTMDBIdsService:
    @classmethod
    def build_querys(self, raw_item: RawItem) -> Generator[str]:
        if raw_item["title"] and raw_item["year"]:
            yield f"{raw_item['title']} {raw_item['year']}"
        if raw_item["translated_title"] and raw_item["year"]:
            yield f"{raw_item['translated_title']} {raw_item['year']}"
        if raw_item["title"]:
            yield raw_item["title"]
        if raw_item["translated_title"]:
            yield raw_item["translated_title"]

    @classmethod
    async def best_determines_option(
        self, determines_generator: DeterminesGenerator
    ) -> Tuple[Optional[str], Optional[ItemType]]:
        best_s, best_v, best_t = 0.0, None, None
        async for s, v, t in determines_generator:
            if s <= best_s:
                continue
            best_s, best_v, best_t = s, v, t
        return best_v, best_t

    def __init__(self):
        self.imdb_suggestion_api = IMDbSuggestionAPI()
        self.tmdb_trending_api = TMDBTrendingAPI()

    async def determines(
        self, raw_item: RawItem
    ) -> Tuple[Optional[str], Optional[str], Optional[ItemType]]:
        imdb_id, imdb_item_type = (
            await DeterminesIMDbTMDBIdsService.best_determines_option(
                self.determines_imdb_id(raw_item)
            )
        )
        tmdb_id, _ = await DeterminesIMDbTMDBIdsService.best_determines_option(
            self.determines_tmdb_id(raw_item, imdb_item_type)
        )
        return imdb_id, tmdb_id, imdb_item_type

    async def determines_imdb_id(self, raw_item: RawItem) -> DeterminesGenerator:
        for query in DeterminesIMDbTMDBIdsService.build_querys(raw_item):
            try:
                data = await self.imdb_suggestion_api.execute(query)
            except IMDbSuggestionAPIError:
                continue
            for item in data["d"]:
                if "qid" not in item.keys():
                    continue
                similarity = jaccard_similarity(
                    item["l"],
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                qid = item.get("qid")
                if qid == "movie":
                    yield similarity, item["id"], ItemType.movie
                if qid == "tvSeries":
                    yield similarity, item["id"], ItemType.tv

    async def determines_tmdb_id(
        self, raw_item: RawItem, force_item_type: Optional[ItemType] = None
    ) -> DeterminesGenerator:
        for query in DeterminesIMDbTMDBIdsService.build_querys(raw_item):
            try:
                data = await self.tmdb_trending_api.execute(query)
            except TMDBTrendingAPIError:
                continue
            for result in data["results"]:
                if isinstance(result, str):
                    continue
                similarity = jaccard_similarity(
                    result["name"],
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                if result["media_type"] == "movie" and (
                    not force_item_type or force_item_type == ItemType.movie
                ):
                    yield similarity, str(result["id"]), ItemType.movie
                if result["media_type"] == "tv" and (
                    not force_item_type or force_item_type == ItemType.tv
                ):
                    yield similarity, str(result["id"]), ItemType.tv
