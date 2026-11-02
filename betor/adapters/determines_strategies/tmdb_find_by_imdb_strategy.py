from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import ITMDBAPI, ITMDBAPIError
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class TmdbFindByImdbStrategy(Strategy):
    def __init__(self, itmdb_api: ITMDBAPI):
        self.itmdb_api = itmdb_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if imdb_scores:
            for k, score in imdb_scores.items():
                imdb_id, _ = k
                try:
                    response = await self.itmdb_api.get_movie_by_imdb_id(imdb_id)
                    tmdb_id = response.get("tmdb_id") or response.get("id")
                    if tmdb_id:
                        yield self, score, None, str(tmdb_id), ItemType.movie
                        continue
                except ITMDBAPIError:
                    pass
                try:
                    response = await self.itmdb_api.get_tvshow_by_imdb_id(imdb_id)
                    tmdb_id = response.get("tmdb_id") or response.get("id")
                    if tmdb_id:
                        yield self, score, None, str(tmdb_id), ItemType.tv
                except ITMDBAPIError:
                    pass
