from typing import Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import IMDBAPIDevTitleAPI, IMDBAPIDevTitleAPIError
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class RawImdbIdStrategy(Strategy):
    def __init__(self, imdb_title_api: IMDBAPIDevTitleAPI):
        self.imdb_title_api = imdb_title_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        if raw_item["imdb_id"]:
            try:
                title = await self.imdb_title_api.execute(raw_item["imdb_id"])
                if title["type"] == "movie":
                    yield 100.0, title["id"], None, ItemType.movie
                if title["type"] in ["tvSeries", "tvMiniSeries"]:
                    yield 100.0, title["id"], None, ItemType.tv
                return
            except IMDBAPIDevTitleAPIError:
                return
