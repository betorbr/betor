from typing import Optional

from betor.entities import RawItem
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class RawImdbIdStrategy(Strategy):
    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if raw_item["imdb_id"]:
            yield self, 100.0, raw_item["imdb_id"], None, None
