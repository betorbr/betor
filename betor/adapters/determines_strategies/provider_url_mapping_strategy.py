from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import TMDBFindByIdAPI, TMDBFindByIdAPIError
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class ProviderURLMappingStrategy(Strategy):
    def __init__(
        self,
        provider_repo: ProviderURLIMDBMappingRepository,
        tmdb_find_by_id_api: TMDBFindByIdAPI,
    ):
        self.provider_repo = provider_repo
        self.tmdb_find_by_id_api = tmdb_find_by_id_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if provider_url_mapping := await self.provider_repo.get(
            raw_item["provider_url"]
        ):
            try:
                response = await self.tmdb_find_by_id_api.execute(
                    provider_url_mapping["imdb_id"], "imdb_id"
                )
                for movie in response["movie_results"]:
                    yield self, 100.0, provider_url_mapping["imdb_id"], str(
                        movie["id"]
                    ), ItemType.movie
                for tv in response["tv_results"]:
                    yield self, 100.0, provider_url_mapping["imdb_id"], str(
                        tv["id"]
                    ), ItemType.tv
            except TMDBFindByIdAPIError:
                return
