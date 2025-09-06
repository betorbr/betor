import json
from typing import List, Optional, TypedDict, cast

import scrapy
import scrapy.http
import twisted.internet.error

from betor_scrapy.extensions import FlareSolverrExtension


class FlareSolverrSolutionCookie(TypedDict):
    domain: str
    expiry: int
    name: str
    value: str


class FlareSolverrSolution(TypedDict):
    url: str
    status: int
    cookies: List[FlareSolverrSolutionCookie]
    userAgent: str
    headers: dict
    response: str


class CloudflareDownloaderMiddleware:
    def solves_cloudflare(
        self,
        spider: scrapy.Spider,
        request: scrapy.Request,
        response_flags: List[str] = [],
    ):
        flaresolverr_base_url: Optional[str] = spider.crawler.settings.get(
            "FLARESOLVERR_BASE_URL"
        )
        if not flaresolverr_base_url:
            spider.logger.warning("Skip FlareSolverr, base URL not setted!")
            return None
        flaresolverr: Optional[FlareSolverrExtension] = getattr(
            spider, "flaresolverr", None
        )
        assert flaresolverr, "Flaresolverr extension not initialized"
        cf_clearance_domain = request.meta.get("cf_clearance_domain")
        if cf_clearance_domain and (
            requests_session := flaresolverr.get_cf_clearance_session(
                cf_clearance_domain
            )
        ):
            spider.logger.info("Try solve with CF clearance...")
            try:
                res = requests_session.get(request.url)
                if res.ok:
                    return scrapy.http.HtmlResponse(
                        url=request.url,
                        status=res.status_code,
                        headers=res.headers,
                        body=res.text,
                        request=request,
                        encoding="utf-8",
                        flags=["cf_clearance", *response_flags],
                    )
            except Exception as e:
                spider.logger.error("Failed to solve with CF clearance: %s", e)
        session, session_lock = flaresolverr.get_free_session()
        return scrapy.http.Request(
            f"{flaresolverr_base_url}/v1",
            request.callback,
            "POST",
            {"Content-type": "application/json"},
            json.dumps(
                {
                    "cmd": f"request.{request.method.lower()}",
                    "url": request.url,
                    "session": session,
                }
            ),
            meta={
                "allow_offsite": True,
                "flaresolverr_session": session,
                "flaresolverr_session_lock": session_lock,
                "original_request": request,
                **request.meta,
            },
            errback=request.errback,
            flags=["flaresolverr", *request.flags],
            cb_kwargs=request.cb_kwargs,
        )

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
        if r := self.solves_cloudflare(spider, request, response_flags=response.flags):
            return r
        return response

    def process_exception(
        self, request: scrapy.Request, exception: Exception, spider: scrapy.Spider
    ):
        if isinstance(exception, twisted.internet.error.ConnectionRefusedError):
            spider.logger.info(
                "Trying solves with Cloudflare. Using FlareSolverr on URL: %s",
                request.url,
            )
            return self.solves_cloudflare(spider, request)


class CloudflareDownloaderResponseMiddleware:
    def process_response(
        self,
        request: scrapy.http.Request,
        response: scrapy.http.Response,
        spider: scrapy.Spider,
    ):
        if "flaresolverr" not in request.flags and "flaresolverr" in response.flags:
            return response
        flaresolverr: Optional[FlareSolverrExtension] = getattr(
            spider, "flaresolverr", None
        )
        assert flaresolverr, "Flaresolverr extension not initialized"
        if session_lock := request.meta.pop("flaresolverr_session_lock", None):
            flaresolverr.free_session(session_lock)
        if response.status != 200:
            return response
        data: dict = json.loads(response.body)
        data_solution = cast(Optional[FlareSolverrSolution], data.get("solution"))
        assert data_solution, "FlareSolverr solution empty"
        for cookie in data_solution["cookies"]:
            if cookie["name"] != "cf_clearance":
                continue
            flaresolverr.add_cf_clearance(
                cookie["domain"],
                cookie["value"],
                data_solution["userAgent"],
                expire_at=cookie["expiry"],
            )
        return scrapy.http.HtmlResponse(
            url=data_solution["url"],
            status=data_solution["status"],
            headers=data_solution["headers"],
            body=data_solution["response"],
            request=request,
            encoding="utf-8",
            flags=["flaresolverr", *response.flags],
        )
