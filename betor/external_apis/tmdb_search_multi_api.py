from typing import List, Literal, TypedDict, cast
from urllib.parse import quote

import httpx
from celery import Task
from celery.result import AsyncResult, allow_join_result

from betor.celery.app import celery_app


class TMDBSearchMultiAPIResponseResult(TypedDict):
    id: int
    title: str
    original_title: str


class TMDBSearchMultiAPIResponse(TypedDict):
    results: List[TMDBSearchMultiAPIResponseResult]


class TMDBSearchMultiAPIError(Exception):
    pass


class TMDBSearchMultiAPI:
    def __init__(
        self,
        url: str = "https://api.themoviedb.org/3/search/multi?query={query}&language={language}",
    ):
        self.url = url

    async def execute(
        self, query: str, language: Literal["pt-BR"]
    ) -> TMDBSearchMultiAPIResponse:
        task: Task = celery_app.signature("tmdb_api_request")
        task_result: AsyncResult = task.apply_async(
            args=(self.url.format(query=quote(query), language=language),),
        )
        try:
            with allow_join_result():
                response = task_result.get()
        except httpx.HTTPStatusError as e:
            raise TMDBSearchMultiAPIError() from e
        return cast(TMDBSearchMultiAPIResponse, response)
