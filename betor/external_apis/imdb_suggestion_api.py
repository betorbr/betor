from typing import List, Literal, Optional, TypedDict, Union, cast
from urllib.parse import quote

import httpx


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
