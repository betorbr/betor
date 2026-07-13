import logging
from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBSearchMultiAPI
from betor.settings import tmdb_api_settings
from betor.types import Scores, StrategyGenerator
from betor.utils import jaccard_similarity

from .strategy import Strategy

logger = logging.getLogger(__name__)


class TmdbTranslatedTitleSearchStrategy(Strategy):
    def __init__(self, tmdb_search_multi_api: TMDBSearchMultiAPI):
        self.tmdb_search_multi_api = tmdb_search_multi_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if not raw_item["translated_title"]:
            logger.debug(
                "Skipping TmdbTranslatedTitleSearchStrategy due to missing translated title"
            )
            return
        if not tmdb_api_settings.access_token:
            logger.warning(
                "Skipping TmdbTranslatedTitleSearchStrategy due to missing TMDb API token"
            )
            return
        response = await self.tmdb_search_multi_api.execute(
            raw_item["translated_title"], "pt-BR"
        )
        for result in response["results"]:
            title_name = result.get("title") or result.get("name")
            if not title_name:
                continue
            similarity = jaccard_similarity(
                title_name,
                raw_item["translated_title"],
            )
            if similarity < 0.95:
                break
            if result["media_type"] == "movie":
                yield self, similarity * 100, None, str(result["id"]), ItemType.movie
            elif result["media_type"] == "tv":
                yield self, similarity * 100, None, str(result["id"]), ItemType.tv
