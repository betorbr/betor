import logging
from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import ITMDBAPI, ITMDBAPIError
from betor.types import Scores, StrategyGenerator
from betor.utils import jaccard_similarity

from .strategy import Strategy

logger = logging.getLogger(__name__)


class TmdbTranslatedTitleSearchStrategy(Strategy):
    def __init__(self, itmdb_api: ITMDBAPI):
        self.itmdb_api = itmdb_api

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
        try:
            results = await self.itmdb_api.search(raw_item["translated_title"], "pt-BR")
        except ITMDBAPIError:
            return
        for result in results:
            title_name = result.get("title") or result.get("original_title")
            if not title_name:
                continue
            similarity = jaccard_similarity(
                title_name,
                raw_item["translated_title"],
            )
            if similarity < 0.95:
                break
            media_type = result.get("media_type")
            tmdb_id = result.get("tmdb_id") or result.get("id")
            if not tmdb_id:
                continue
            if media_type == "movie":
                yield self, similarity * 100, None, str(tmdb_id), ItemType.movie
            elif media_type == "tv":
                yield self, similarity * 100, None, str(tmdb_id), ItemType.tv
