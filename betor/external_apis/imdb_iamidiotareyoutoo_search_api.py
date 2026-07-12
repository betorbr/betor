from typing import List, TypedDict, cast
from urllib.parse import quote

import httpx

IMDBIAmIdiotAreYouTooSearchAPIResponseDescriptionItem = TypedDict(
    "IMDBIAmIdiotAreYouTooSearchAPIResponseDescriptionItem",
    {
        "#TITLE": str,
        "#YEAR": int,
        "#IMDB_ID": str,
    },
)


class IMDBIAmIdiotAreYouTooSearchAPIResponse(TypedDict):
    ok: bool
    description: List[IMDBIAmIdiotAreYouTooSearchAPIResponseDescriptionItem]


class IMDBIAmIdiotAreYouTooSearchAPIError(Exception):
    pass


class IMDBIAmIdiotAreYouTooSearchAPI:
    def __init__(
        self, url: str = "https://imdb.iamidiotareyoutoo.com/search?q={query}"
    ):
        self.url = url

    async def execute(self, query: str) -> IMDBIAmIdiotAreYouTooSearchAPIResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url.format(query=quote(query)))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise IMDBIAmIdiotAreYouTooSearchAPIError() from e
        data = response.json()
        return cast(IMDBIAmIdiotAreYouTooSearchAPIResponse, data)
