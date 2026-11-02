import logging
from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import ITMDBAPI, ITMDBAPIError
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy

logger = logging.getLogger(__name__)


class ImdbFindByTmdbStrategy(Strategy):
    def __init__(self, itmdb_api: ITMDBAPI):
        self.itmdb_api = itmdb_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if not tmdb_scores:
            logger.debug("Skipping ImdbFindByTmdbStrategy due to missing TMDB scores")
            return

        for k, score in tmdb_scores.items():
            tmdb_id, item_type = k
            if not item_type:
                continue
            try:
                if item_type == ItemType.movie:
                    response = await self.itmdb_api.get_movie_by_tmdb_id(tmdb_id)
                elif item_type == ItemType.tv:
                    response = await self.itmdb_api.get_tvshow_by_tmdb_id(tmdb_id)
                else:
                    continue
            except ITMDBAPIError:
                return
            imdb_id = response.get("imdb_id")
            if imdb_id:
                yield self, score, imdb_id, None, item_type
