from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import IMDBAPIDevTitleAPI, IMDBAPIDevTitleAPIError
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class ProviderURLMappingStrategy(Strategy):
    def __init__(
        self,
        provider_repo: ProviderURLIMDBMappingRepository,
        imdb_title_api: IMDBAPIDevTitleAPI,
    ):
        self.provider_repo = provider_repo
        self.imdb_title_api = imdb_title_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        if provider_url_mapping := await self.provider_repo.get(
            raw_item["provider_url"]
        ):
            try:
                title = await self.imdb_title_api.execute(
                    provider_url_mapping["imdb_id"]
                )
                if title["type"] == "movie":
                    yield 100.0, title["id"], None, ItemType.movie
                if title["type"] in ["tvSeries", "tvMiniSeries"]:
                    yield 100.0, title["id"], None, ItemType.tv
                return
            except IMDBAPIDevTitleAPIError:
                return
