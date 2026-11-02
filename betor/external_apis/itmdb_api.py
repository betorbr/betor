from typing import List, Optional, TypedDict, Union, cast

import httpx

from betor.settings import itmdb_api_settings


class ITMDBItemResponse(TypedDict):
    id: str
    title: str
    original_title: Optional[str]
    year: Optional[int]
    overview: Optional[str]
    tmdb_poster_path: Optional[str]
    tmdb_backdrop_path: Optional[str]
    imdb_id: Optional[str]
    tmdb_id: Optional[int]
    media_type: Optional[str]


class ITMDBSearchItemResponse(TypedDict):
    id: str
    title: str
    original_title: Optional[str]
    year: Optional[int]
    overview: Optional[str]
    tmdb_poster_path: Optional[str]
    tmdb_backdrop_path: Optional[str]
    imdb_id: Optional[str]
    tmdb_id: Optional[int]
    media_type: Optional[str]


class ITMDBAPIError(Exception):
    pass


class ITMDBAPI:
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = base_url or itmdb_api_settings.url
        self.timeout = timeout or itmdb_api_settings.timeout

    async def get_movie_by_imdb_id(
        self, imdb_id: str, language: str = "en", timeout: Optional[int] = None
    ) -> ITMDBItemResponse:
        url = f"{self.base_url.rstrip('/')}/v1/movies/tt{imdb_id.removeprefix('tt')}"
        t = timeout if timeout is not None else self.timeout
        params: dict[str, Union[str, int]] = {"language": language, "timeout": t}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return cast(ITMDBItemResponse, response.json())
            except httpx.HTTPStatusError as e:
                raise ITMDBAPIError(f"Error fetching movie by imdb_id {imdb_id}") from e

    async def get_movie_by_tmdb_id(
        self,
        tmdb_id: Union[str, int],
        language: str = "en-US",
        timeout: Optional[int] = None,
    ) -> ITMDBItemResponse:
        url = f"{self.base_url.rstrip('/')}/v1/movies/{tmdb_id}"
        t = timeout if timeout is not None else self.timeout
        params: dict[str, Union[str, int]] = {"language": language, "timeout": t}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return cast(ITMDBItemResponse, response.json())
            except httpx.HTTPStatusError as e:
                raise ITMDBAPIError(f"Error fetching movie by tmdb_id {tmdb_id}") from e

    async def get_tvshow_by_imdb_id(
        self, imdb_id: str, language: str = "en", timeout: Optional[int] = None
    ) -> ITMDBItemResponse:
        url = f"{self.base_url.rstrip('/')}/v1/tvshows/tt{imdb_id.removeprefix('tt')}"
        t = timeout if timeout is not None else self.timeout
        params: dict[str, Union[str, int]] = {"language": language, "timeout": t}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return cast(ITMDBItemResponse, response.json())
            except httpx.HTTPStatusError as e:
                raise ITMDBAPIError(
                    f"Error fetching tvshow by imdb_id {imdb_id}"
                ) from e

    async def get_tvshow_by_tmdb_id(
        self,
        tmdb_id: Union[str, int],
        language: str = "en-US",
        timeout: Optional[int] = None,
    ) -> ITMDBItemResponse:
        url = f"{self.base_url.rstrip('/')}/v1/tvshows/{tmdb_id}"
        t = timeout if timeout is not None else self.timeout
        params: dict[str, Union[str, int]] = {"language": language, "timeout": t}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return cast(ITMDBItemResponse, response.json())
            except httpx.HTTPStatusError as e:
                raise ITMDBAPIError(
                    f"Error fetching tvshow by tmdb_id {tmdb_id}"
                ) from e

    async def search(
        self, query: str, language: str = "en-US", timeout: Optional[int] = None
    ) -> List[ITMDBSearchItemResponse]:
        url = f"{self.base_url.rstrip('/')}/v1/search"
        t = timeout if timeout is not None else self.timeout
        params: dict[str, Union[str, int]] = {
            "q": query,
            "language": language,
            "timeout": t,
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return cast(List[ITMDBSearchItemResponse], response.json())
            except httpx.HTTPStatusError as e:
                raise ITMDBAPIError(f"Error searching query {query}") from e
