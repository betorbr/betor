import logging
from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBExternalIdsAPI, TMDBExternalIdsAPIError
from betor.settings import tmdb_api_settings
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy

logger = logging.getLogger(__name__)


class ImdbFindByTmdbStrategy(Strategy):
    def __init__(self, tmdb_external_ids_api: TMDBExternalIdsAPI):
        self.tmdb_external_ids_api = tmdb_external_ids_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if not tmdb_scores:
            logger.debug("Skipping ImdbFindByTmdbStrategy due to missing TMDBb scores")
            return

        if not tmdb_api_settings.access_token:
            logger.warning(
                "Skipping ImdbFindByTmdbStrategy due to missing TMDb API token"
            )
            return

        for k, score in tmdb_scores.items():
            tmdb_id, item_type = k
            if not item_type:
                continue
            try:
                if item_type == ItemType.movie:
                    response = await self.tmdb_external_ids_api.execute(
                        "movie", tmdb_id
                    )
                elif item_type == ItemType.tv:
                    response = await self.tmdb_external_ids_api.execute("tv", tmdb_id)
                else:
                    continue
            except TMDBExternalIdsAPIError:
                return
            yield self, score, response["imdb_id"], None, item_type
