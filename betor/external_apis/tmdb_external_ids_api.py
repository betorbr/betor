from typing import Literal, Optional, TypedDict, cast

import httpx
from celery import Task
from celery.result import AsyncResult, allow_join_result

from betor.celery.app import celery_app


class TMDBExternalIdsResponse(TypedDict):
    imdb_id: Optional[str]


class TMDBExternalIdsAPIError(Exception):
    pass


class TMDBExternalIdsAPI:
    def __init__(
        self,
        url: str = "https://api.themoviedb.org/3/{item_type}/{tmdb_id}/external_ids",
    ):
        self.url = url

    async def execute(
        self, item_type: Literal["movie", "tv"], tmdb_id: str
    ) -> TMDBExternalIdsResponse:
        task: Task = celery_app.signature("tmdb_api_request")
        task_result: AsyncResult = task.apply_async(
            args=(self.url.format(item_type=item_type, tmdb_id=tmdb_id),),
        )
        try:
            with allow_join_result():
                response = task_result.get()
        except httpx.HTTPStatusError as e:
            raise TMDBExternalIdsAPIError() from e
        return cast(TMDBExternalIdsResponse, response)
