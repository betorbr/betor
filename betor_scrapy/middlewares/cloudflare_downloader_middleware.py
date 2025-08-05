import json
from typing import Optional, TypedDict

import scrapy
import scrapy.http

from betor_scrapy.extension import FlareSolverrExtension


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
        if "flaresolverr" in request.flags:
            return response
        if not (
            response.status == 403
            and response.xpath("//title/text()").get() == "Just a moment..."
        ):
            return response
        spider.logger.info(
            "Cloudflare detected. Using FlareSolverr on URL: %s", request.url
        )
        flaresolverr_base_url: Optional[str] = spider.crawler.settings.get(
            "FLARESOLVERR_BASE_URL"
        )
        if not flaresolverr_base_url:
            spider.logger.warning("Skip FlareSolverr, base URL not setted!")
            return response
        flaresolverr: Optional[FlareSolverrExtension] = getattr(spider, "flaresolverr")
        session = flaresolverr.get_free_session() if flaresolverr else None
        return scrapy.http.Request(
            f"{flaresolverr_base_url}/v1",
            request.callback,
            "POST",
            {"Content-type": "application/json"},
            json.dumps(
                {
                    "cmd": f"request.{request.method.lower()}",
                    "url": request.url,
                    **({"session": session} if session else {}),
                }
            ),
            meta={
                "allow_offsite": True,
                "flaresolverr_session": session,
                **request.meta,
            },
            errback=request.errback,
            flags=["flaresolverr", *request.flags],
            cb_kwargs=request.cb_kwargs,
        )


class CloudflareDownloaderResponseMiddleware:
    def process_response(
        self,
        request: scrapy.http.Request,
        response: scrapy.http.Response,
        spider: scrapy.Spider,
    ):
        if "flaresolverr" not in request.flags or "flaresolverr" in response.flags:
            return response
        if session := request.meta.get("flaresolverr_session"):
            flaresolverr: Optional[FlareSolverrExtension] = getattr(
                spider, "flaresolverr"
            )
            if flaresolverr:
                flaresolverr.free_session(session)
        if response.status != 200:
            return response
        data: dict = json.loads(response.body)
        data_solution: Optional[FlareSolverrSolutionType] = data.get("solution")
        assert data_solution, "FlareSolverr Solution empty"
        return scrapy.http.HtmlResponse(
            url=data_solution["url"],
            status=data_solution["status"],
            headers=data_solution["headers"],
            body=data_solution["response"],
            request=request,
            encoding="utf-8",
            flags=["flaresolverr", *response.flags],
        )
