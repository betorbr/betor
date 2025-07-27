from typing import Optional, TypedDict

import requests
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
        flaresolverr_response = requests.post(
            f"{flaresolverr_settings.base_url}/v1",
            json={
                "cmd": f"request.{request.method.lower()}",
                "url": request.url,
            },
        )
        flaresolverr_response.raise_for_status()
        flaresolverr_data: dict = flaresolverr_response.json()
        flaresolverr_data_status = flaresolverr_data.get("status")
        assert (
            flaresolverr_data_status == "ok"
        ), f"FlareSolverr status {flaresolverr_data_status}"
        flaresolverr_data_solution: Optional[FlareSolverrSolutionType] = (
            flaresolverr_data.get("solution")
        )
        assert flaresolverr_data_solution, "FlareSolverr Solution empty"
        return scrapy.http.TextResponse(
            url=flaresolverr_data_solution["url"],
            status=flaresolverr_data_solution["status"],
            headers=flaresolverr_data_solution["headers"],
            body=flaresolverr_data_solution["response"],
            request=request,
            encoding="utf-8",
        )
