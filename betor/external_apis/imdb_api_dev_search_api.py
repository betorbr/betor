from typing import List, Literal, TypedDict, cast
from urllib.parse import quote

import httpx


class IMDBAPIDevSearchAPIResponseTitle(TypedDict):
    id: str
    type: Literal["movie", "tvSeries", "tvMiniSeries"]
    originalTitle: str


class IMDBAPIDevSearchAPIResponse(TypedDict):
    titles: List[IMDBAPIDevSearchAPIResponseTitle]


class IMDBAPIDevSearchAPIError(Exception):
    pass


class IMDBAPIDevSearchAPI:
    def __init__(
        self, url: str = "https://api.imdbapi.dev/search/titles?query={query}"
    ):
        self.url = url

    async def execute(self, query: str) -> IMDBAPIDevSearchAPIResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url.format(query=quote(query)))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise IMDBAPIDevSearchAPIError() from e
        return cast(IMDBAPIDevSearchAPIResponse, response.json())
