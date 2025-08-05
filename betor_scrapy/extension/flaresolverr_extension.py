from typing import Self, Set, TypedDict, cast

import httpx
import scrapy.crawler
import scrapy.exceptions
import scrapy.signals


class FlareSolverrSessionsCreateResponse(TypedDict):
    session: str


class FlareSolverrExtension:
    free_sessions: Set[str]
    locked_sessions: Set[str]

    def __init__(
        self,
        flaresolverr_base_url: str,
        free_sessions: Set[str],
        locked_sessions: Set[str],
    ):
        self.flaresolverr_base_url = flaresolverr_base_url
        self.free_sessions = free_sessions
        self.locked_sessions = locked_sessions

    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler) -> Self:
        flaresolverr_base_url = crawler.settings.get("FLARESOLVERR_BASE_URL")
        if not flaresolverr_base_url:
            raise scrapy.exceptions.NotConfigured
        obj = cls(flaresolverr_base_url, set(), set())
        crawler.signals.connect(obj.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=scrapy.signals.spider_closed)
        return obj

    def spider_opened(self, spider: scrapy.Spider) -> None:
        spider.flaresolverr = self  # type: ignore[attr-defined]

    def spider_closed(self, spider: scrapy.Spider) -> None:
        sessions = {*self.free_sessions, *self.locked_sessions}
        for session in sessions:
            response = httpx.post(
                f"{self.flaresolverr_base_url}/v1",
                json={"cmd": "sessions.destroy", "session": session},
            )
            response.raise_for_status()

    def get_free_session(self) -> str:
        if not self.free_sessions:
            self.create_session()
            return self.get_free_session()
        session = self.free_sessions.pop()
        self.locked_sessions.add(session)
        return session

    def create_session(self):
        response = httpx.post(
            f"{self.flaresolverr_base_url}/v1", json={"cmd": "sessions.create"}
        )
        response.raise_for_status()
        data = cast(FlareSolverrSessionsCreateResponse, response.json())
        self.free_sessions.add(data["session"])

    def free_session(self, session: str):
        self.locked_sessions.remove(session)
        self.free_sessions.add(session)
