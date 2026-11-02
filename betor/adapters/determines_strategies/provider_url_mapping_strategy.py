from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import ITMDBAPI, ITMDBAPIError
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class ProviderURLMappingStrategy(Strategy):
    def __init__(
        self,
        provider_repo: ProviderURLIMDBMappingRepository,
        itmdb_api: ITMDBAPI,
    ):
        self.provider_repo = provider_repo
        self.itmdb_api = itmdb_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if provider_url_mapping := await self.provider_repo.get(
            raw_item["provider_url"]
        ):
            imdb_id = provider_url_mapping["imdb_id"]
            try:
                response = await self.itmdb_api.get_movie_by_imdb_id(imdb_id)
                tmdb_id = response.get("tmdb_id") or response.get("id")
                if tmdb_id:
                    yield self, 100.0, imdb_id, str(tmdb_id), ItemType.movie
            except ITMDBAPIError:
                pass
            try:
                response = await self.itmdb_api.get_tvshow_by_imdb_id(imdb_id)
                tmdb_id = response.get("tmdb_id") or response.get("id")
                if tmdb_id:
                    yield self, 100.0, imdb_id, str(tmdb_id), ItemType.tv
            except ITMDBAPIError:
                pass
