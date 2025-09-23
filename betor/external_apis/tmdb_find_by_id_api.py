from typing import List, Literal, TypedDict, cast

import httpx

from betor.settings import tmdb_api_settings


class TMDBFindByIdResponseResult(TypedDict):
    adult: bool
    backdrop_path: str
    poster_path: str
    id: int
    original_language: str
    overview: str
    genre_ids: List[int]
    popularity: float
    vote_average: float
    vote_count: int


class TMDBFindByIdResponseMovieResult(TMDBFindByIdResponseResult):
    title: str
    original_title: str
    media_type: Literal["movie"]
    release_date: str
    video: bool


class TMDBFindByIdResponseTVResult(TMDBFindByIdResponseResult):
    name: str
    original_name: str
    media_type: Literal["tv"]
    first_air_date: str
    origin_country: List[str]


class TMDBFindByIdResponse(TypedDict):
    movie_results: List[TMDBFindByIdResponseMovieResult]
    tv_results: List[TMDBFindByIdResponseTVResult]


class TMDBFindByIdAPIError(Exception):
    pass


class TMDBFindByIdAPI:
    def __init__(
        self,
        url: str = "https://api.themoviedb.org/3/find/{external_id}?external_source={external_source}",
    ):
        self.url = url

    async def execute(self, external_id: str, external_source: Literal["imdb_id"]):
        assert tmdb_api_settings.access_token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.url.format(
                    external_id=external_id, external_source=external_source
                ),
                headers={"Authorization": f"Bearer {tmdb_api_settings.access_token}"},
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise TMDBFindByIdAPIError() from e
        return cast(TMDBFindByIdResponse, response.json())
