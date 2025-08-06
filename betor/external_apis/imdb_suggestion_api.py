from typing import Generator, List, Literal, Optional, Tuple, TypedDict, Union, cast
from urllib.parse import quote

import httpx

from betor.types import ItemType


class IMDbSuggestionResponseImage(TypedDict):
    width: int
    height: int
    imageUrl: str


class IMDbSuggestionResponseTitle(TypedDict):
    i: Optional[IMDbSuggestionResponseImage]
    id: str
    l: str
    q: str
    qid: Literal["tvSeries", "movie"]
    rank: int
    s: str
    y: int


class IMDbSuggestionResponseLink(TypedDict):
    i: Optional[IMDbSuggestionResponseImage]
    id: str
    l: str
    s: str


class IMDbSuggestionResponse(TypedDict):
    d: List[Union[IMDbSuggestionResponseTitle, IMDbSuggestionResponseLink]]
    q: str
    v: int


class IMDbSuggestionAPIError(Exception):
    pass


class IMDbSuggestionAPI:
    def __init__(
        self, url: str = "https://v3.sg.media-imdb.com/suggestion/x/{query}.json"
    ):
        self.url = url

    async def execute(self, query: str) -> IMDbSuggestionResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url.format(query=quote(query)))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise IMDbSuggestionAPIError() from e
        return cast(IMDbSuggestionResponse, response.json())

    async def determines_imdb_id(
        self,
        title: Optional[str] = None,
        translated_title: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Optional[Tuple[str, ItemType]]:
        if not title and not translated_title:
            raise ValueError("Without enough information to determine IMDb ID")
        for query in self.determines_imdb_id_querys(title, translated_title, year):
            data = await self.execute(query)
            for item in data["d"]:
                if "qid" not in item.keys():
                    continue
                qid = item.get("qid")
                if qid == "movie":
                    return item["id"], ItemType.movie
                if qid == "tvSeries":
                    return item["id"], ItemType.tv
        return None

    def determines_imdb_id_querys(
        self,
        title: Optional[str] = None,
        translated_title: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Generator[str]:
        if title and year:
            yield f"{title} {year}"
        if translated_title and year:
            yield f"{translated_title} {year}"
        if title:
            yield title
        if translated_title:
            yield translated_title
