from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBFindByIdAPI
from betor.settings import tmdb_api_settings
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class TmdbFindByImdbStrategy(Strategy):
    def __init__(self, tmdb_find_by_id_api: TMDBFindByIdAPI):
        self.tmdb_find_by_id_api = tmdb_find_by_id_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        if imdb_scores and tmdb_api_settings.access_token:
            for k, score in imdb_scores.items():
                imdb_id, _ = k
                try:
                    response = await self.tmdb_find_by_id_api.execute(
                        imdb_id, "imdb_id"
                    )
                except Exception:
                    return
                results = response.get("movie_results", []) + response.get(
                    "tv_results", []
                )
                for result in results:
                    tmdb_id = str(result.get("id"))
                    item_type = (
                        result.get("media_type") == "movie"
                        and ItemType.movie
                        or result.get("media_type") == "tv"
                        and ItemType.tv
                    )
                    if tmdb_id and item_type:
                        yield score, None, tmdb_id, item_type
                        break
