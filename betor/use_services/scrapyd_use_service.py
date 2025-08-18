from typing import Literal, OrderedDict, TypeAlias, TypedDict, cast
from urllib.parse import urlencode

import httpx

from betor.settings import scrapyd_settings

ScrapydStatus: TypeAlias = Literal["ok"]


class ScrapydError(Exception):
    pass


class ScrapydScheduleResponse(TypedDict):
    status: ScrapydStatus
    jobid: str
    node_name: str


class ScrapydStatusResponse(TypedDict):
    status: ScrapydStatus
    node_name: str
    currstate: Literal["pending", "running", "finished"]


class ScrapydUseService:
    async def schedule(
        self, project: str, spider: str, **kwargs
    ) -> ScrapydScheduleResponse:
        async with httpx.AsyncClient(base_url=scrapyd_settings.base_url) as client:
            response = await client.post(
                "/schedule.json", data={"project": project, "spider": spider, **kwargs}
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ScrapydError() from e
        return cast(ScrapydScheduleResponse, response.json())

    async def status(self, id: str) -> ScrapydStatusResponse:
        qs = urlencode(OrderedDict(job=id))
        async with httpx.AsyncClient(base_url=scrapyd_settings.base_url) as client:
            response = await client.get(f"/status.json?{qs}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ScrapydError() from e
        return cast(ScrapydStatusResponse, response.json())
