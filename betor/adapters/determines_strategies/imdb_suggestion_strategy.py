from typing import Optional, cast

from betor.entities import RawItem
from betor.enums import ItemType
from betor.external_apis import (
    IMDbSuggestionAPI,
    IMDbSuggestionAPIError,
    IMDbSuggestionResponseTitle,
)
from betor.types import Scores, StrategyGenerator

from .strategy import Strategy


class ImdbSuggestionStrategy(Strategy):
    def __init__(self, imdb_suggestion_api: IMDbSuggestionAPI):
        self.imdb_suggestion_api = imdb_suggestion_api

    async def __call__(
        self,
        raw_item: RawItem,
        imdb_scores: Optional[Scores] = None,
        tmdb_scores: Optional[Scores] = None,
    ) -> StrategyGenerator[ItemType]:
        if raw_item["translated_title"] and raw_item["cast"] and not raw_item["title"]:
            try:
                suggestions = await self.imdb_suggestion_api.execute(
                    raw_item["translated_title"]
                )
                for suggestion in suggestions["d"]:
                    if not suggestion.get("qid"):
                        continue
                    s = cast(IMDbSuggestionResponseTitle, suggestion)
                    suggestion_cast = set(
                        [v.strip() for v in s.get("s", "").split(",")]
                    )
                    raw_item_cast = set(raw_item["cast"])
                    if suggestion_cast.intersection(raw_item_cast):
                        if s["qid"] == "movie":
                            yield 50.0, s["id"], None, ItemType.movie
                        if s["qid"] in ["tvSeries", "tvMiniSeries"]:
                            yield 50.0, s["id"], None, ItemType.tv
            except IMDbSuggestionAPIError:
                return
