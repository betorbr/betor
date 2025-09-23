from typing import List, Literal, TypedDict, cast

import httpx
from celery import Task
from celery.result import AsyncResult, allow_join_result

from betor.celery.app import celery_app


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
        task: Task = celery_app.signature("tmdb_api_request")
        task_result: AsyncResult = task.apply_async(
            args=(
                self.url.format(
                    external_id=external_id, external_source=external_source
                ),
            ),
        )
        try:
            with allow_join_result():
                response = task_result.get()
        except httpx.HTTPStatusError as e:
            raise TMDBFindByIdAPIError() from e
        return cast(TMDBFindByIdResponse, response)
