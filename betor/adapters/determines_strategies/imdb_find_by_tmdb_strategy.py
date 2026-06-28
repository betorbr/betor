from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBExternalIdsAPI, TMDBExternalIdsAPIError
from betor.settings import tmdb_api_settings
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class ImdbFindByTmdbStrategy(Strategy):
    def __init__(self, tmdb_external_ids_api: TMDBExternalIdsAPI):
        self.tmdb_external_ids_api = tmdb_external_ids_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        if tmdb_scores and tmdb_api_settings.access_token:
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
                        response = await self.tmdb_external_ids_api.execute(
                            "tv", tmdb_id
                        )
                    else:
                        continue
                except TMDBExternalIdsAPIError:
                    return
                yield score, response["imdb_id"], None, item_type
