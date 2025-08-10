from typing import List, Literal, TypedDict, Union, cast
from urllib.parse import quote

import httpx


class TMDBTrendingResponseResultTitle(TypedDict):
    adult: bool
    backdrop_path: str
    genre_ids: List[int]
    id: int
    original_language: str
    original_name: str
    overview: str
    popularity: float
    poster_path: str
    release_date: str
    name: str
    video: bool
    vote_average: float
    vote_count: int
    media_id: str
    media_type: Literal["movie", "tv"]


class TMDBTrendingResponse(TypedDict):
    results: List[Union[TMDBTrendingResponseResultTitle, str]]


class TMDBTrendingAPIError(Exception):
    pass


class TMDBTrendingAPI:
    def __init__(
        self, url: str = "https://www.themoviedb.org/search/trending?query={query}"
    ):
        self.url = url

    async def execute(self, query: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url.format(query=quote(query)))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TMDBTrendingAPIError() from e
        return cast(TMDBTrendingResponse, response.json())
