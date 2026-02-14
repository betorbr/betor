from typing import AsyncGenerator, Generator, Optional, Tuple, cast

import motor.motor_asyncio

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import (
    IMDBAPIDevSearchAPI,
    IMDBAPIDevSearchAPIError,
    IMDBAPIDevTitleAPI,
    IMDBAPIDevTitleAPIError,
    IMDbSuggestionAPI,
    IMDbSuggestionAPIError,
    IMDbSuggestionResponseTitle,
    TMDBFindByIdAPI,
    TMDBTrendingAPI,
    TMDBTrendingAPIError,
)
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.settings import tmdb_api_settings
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
            if "/" in raw_item["title"]:
                yield from map(lambda v: v.strip(), raw_item["title"].split("/"))
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

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.imdb_api_dev_search_api = IMDBAPIDevSearchAPI()
        self.imdb_api_dev_title_api = IMDBAPIDevTitleAPI()
        self.tmdb_trending_api = TMDBTrendingAPI()
        self.tmdb_find_by_id_api = TMDBFindByIdAPI()
        self.imdb_suggestion_api = IMDbSuggestionAPI()
        self.provider_url_imdb_mapping_repository = ProviderURLIMDBMappingRepository(
            mongodb_client
        )

    async def determines(
        self, raw_item: RawItem
    ) -> Tuple[Optional[str], Optional[str], Optional[ItemType]]:
        imdb_id, imdb_item_type = (
            await DeterminesIMDbTMDBIdsService.best_determines_option(
                self.determines_imdb_id(raw_item)
            )
        )
        tmdb_id, _ = await DeterminesIMDbTMDBIdsService.best_determines_option(
            self.determines_tmdb_id(
                raw_item, force_item_type=imdb_item_type, imdb_id=imdb_id
            )
        )
        return imdb_id, tmdb_id, imdb_item_type

    async def determines_imdb_id(self, raw_item: RawItem) -> DeterminesGenerator:
        if provider_url_mapping := await self.provider_url_imdb_mapping_repository.get(
            raw_item["provider_url"]
        ):
            try:
                title = await self.imdb_api_dev_title_api.execute(
                    provider_url_mapping["imdb_id"]
                )
                if title["type"] == "movie":
                    yield 1.0, title["id"], ItemType.movie
                if title["type"] in ["tvSeries", "tvMiniSeries"]:
                    yield 1.0, title["id"], ItemType.tv
                return
            except IMDBAPIDevTitleAPIError:
                pass
        if raw_item["imdb_id"]:
            try:
                title = await self.imdb_api_dev_title_api.execute(raw_item["imdb_id"])
                if title["type"] == "movie":
                    yield 1.0, title["id"], ItemType.movie
                if title["type"] in ["tvSeries", "tvMiniSeries"]:
                    yield 1.0, title["id"], ItemType.tv
                return
            except IMDBAPIDevTitleAPIError:
                pass
        if raw_item["translated_title"] and raw_item["cast"] and not raw_item["title"]:
            try:
                suggestions = await self.imdb_suggestion_api.execute(
                    raw_item["translated_title"]
                )
                for suggestion in suggestions["d"]:
                    if not suggestion.get("qid"):
                        continue
                    s = cast(IMDbSuggestionResponseTitle, suggestion)
                    suggestion_cast = set(
                        [v.strip() for v in s.get("s", "").split(",")]
                    )
                    raw_item_cast = set(raw_item["cast"])
                    if suggestion_cast.intersection(raw_item_cast):
                        if s["qid"] == "movie":
                            yield 1.0, s["id"], ItemType.movie
                        if s["qid"] in ["tvSeries", "tvMiniSeries"]:
                            yield 1.0, s["id"], ItemType.tv
            except IMDbSuggestionAPIError:
                pass
        for query in DeterminesIMDbTMDBIdsService.build_querys(raw_item):
            try:
                data = await self.imdb_api_dev_search_api.execute(query)
            except IMDBAPIDevSearchAPIError:
                continue
            for title in data["titles"]:
                similarity = jaccard_similarity(
                    title["primaryTitle"],
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                if title["type"] == "movie":
                    yield similarity, title["id"], ItemType.movie
                if title["type"] in ["tvSeries", "tvMiniSeries"]:
                    yield similarity, title["id"], ItemType.tv
                similarity = jaccard_similarity(
                    title["originalTitle"],
                    raw_item["title"] or raw_item["translated_title"] or "",
                )
                if title["type"] == "movie":
                    yield similarity, title["id"], ItemType.movie
                if title["type"] in ["tvSeries", "tvMiniSeries"]:
                    yield similarity, title["id"], ItemType.tv

    async def determines_tmdb_id(
        self,
        raw_item: RawItem,
        force_item_type: Optional[ItemType] = None,
        imdb_id: Optional[str] = None,
    ) -> DeterminesGenerator:
        if imdb_id and tmdb_api_settings.access_token:
            response = await self.tmdb_find_by_id_api.execute(imdb_id, "imdb_id")
            results = response["movie_results"] + response["tv_results"]
            for result in results:
                if force_item_type and (
                    (
                        force_item_type == ItemType.movie
                        and result["media_type"] != "movie"
                    )
                    or (force_item_type == ItemType.tv and result["media_type"] != "tv")
                ):
                    continue
                tmdb_id = str(result["id"])
                item_type = (
                    result["media_type"] == "movie"
                    and ItemType.movie
                    or result["media_type"] == "tv"
                    and ItemType.tv
                )
                assert tmdb_id and item_type
                yield 1.0, tmdb_id, item_type
                return
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
