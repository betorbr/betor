from typing import List, Literal, TypedDict, cast

import httpx

from betor.settings import tmdb_api_settings


class TMDBFindByIdResponseResult(TypedDict):
    id: int
    media_type: Literal["movie", "tv"]


class TMDBFindByIdResponse(TypedDict):
    movie_results: List[TMDBFindByIdResponseResult]
    tv_results: List[TMDBFindByIdResponseResult]


class TMDBFindByIdAPIError(Exception):
    pass


class TMDBFindByIdAPI:
    def __init__(
        self,
        url: str = "https://api.themoviedb.org/3/find/{external_id}?external_source={external_source}",
    ):
        self.url = url

    async def execute(
        self, external_id: str, external_source: Literal["imdb_id"]
    ) -> TMDBFindByIdResponse:
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
