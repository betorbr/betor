from abc import ABC, abstractmethod
from typing import Generator, Optional

from betor.entities import RawItem
from betor.enums import ItemType
from betor.types import Scores, StrategyGenerator


class Strategy(ABC):
    @staticmethod
    def build_queries(raw_item: RawItem) -> Generator[str, None, None]:
        if raw_item["title"] and raw_item["year"]:
            yield f"{raw_item['title']} {raw_item['year']}"
        if raw_item["translated_title"] and raw_item["year"]:
            yield f"{raw_item['translated_title']} {raw_item['year']}"
        if raw_item["title"]:
            yield raw_item["title"]
            if "/" in raw_item["title"]:
                yield from map(lambda v: v.strip(), raw_item["title"].split("/"))
        if raw_item["translated_title"]:
            yield raw_item["translated_title"]

    @abstractmethod
    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        if False:  # pragma: no cover
            yield  # type: ignore[unreachable]
        raise NotImplementedError()
