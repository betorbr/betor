import json
from typing import Optional, TypedDict

import scrapy
import scrapy.http

from betor.settings import flaresolverr_settings


class FlareSolverrSolutionType(TypedDict):
    url: str
    status: int
    headers: dict
    response: str


class CloudflareDownloaderMiddleware:
    def process_response(
        self,
        request: scrapy.http.Request,
        response: scrapy.http.Response,
        spider: scrapy.Spider,
    ):
        if not (
            response.status == 403
            and "<title>Just a moment...</title>" in response.text
        ):
            return response
        spider.logger.info(
            "Cloudflare detected. Using FlareSolverr on URL: %s", request.url
        )
        assert flaresolverr_settings.base_url, "FlareSolverr base URL not setted"
        return scrapy.http.Request(
            f"{flaresolverr_settings.base_url}/v1",
            request.callback,
            "POST",
            {"Content-type": "application/json"},
            json.dumps(
                {
                    "cmd": f"request.{request.method.lower()}",
                    "url": request.url,
                }
            ),
            meta={
                "flaresolverr": True,
                **request.meta,
            },
            errback=request.errback,
            cb_kwargs=request.cb_kwargs,
        )


class CloudflareDownloaderResponseMiddleware:
    def process_response(
        self,
        request: scrapy.http.Request,
        response: scrapy.http.Response,
        spider: scrapy.Spider,
    ):
        if not request.meta.get("flaresolverr", False):
            return response
        assert (
            response.status != 200
        ), f"FlareSolverr fails... {response.status=} {response.body=}"
        data: dict = json.loads(response.body)
        data_status = data.get("status")
        assert data_status == "ok", f"FlareSolverr status {data_status}"
        data_solution: Optional[FlareSolverrSolutionType] = data.get("solution")
        assert data_solution, "FlareSolverr Solution empty"
        return scrapy.http.HtmlResponse(
            url=data_solution["url"],
            status=data_solution["status"],
            headers=data_solution["headers"],
            body=data_solution["response"],
            request=request,
            encoding="utf-8",
        )
