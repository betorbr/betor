from abc import ABC, abstractmethod
from typing import Optional

from betor.entities import RawItem
from betor.types import Scores, StrategyGenerator


class Strategy(ABC):
    @abstractmethod
    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator:
        if False:  # pragma: no cover
            yield  # type: ignore[unreachable]
        raise NotImplementedError()
