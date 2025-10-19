from typing import Literal, TypedDict, cast

import httpx


class IMDBAPIDevTitleAPIResponse(TypedDict):
    id: str
    type: Literal["movie", "tvSeries", "tvMiniSeries"]


class IMDBAPIDevTitleAPIError(Exception):
    pass


class IMDBAPIDevTitleAPI:
    def __init__(self, url: str = "https://api.imdbapi.dev/titles/{imdb_id}"):
        self.url = url

    async def execute(self, imdb_id: str) -> IMDBAPIDevTitleAPIResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url.format(imdb_id=imdb_id))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise IMDBAPIDevTitleAPIError() from e
        return cast(IMDBAPIDevTitleAPIResponse, response.json())
