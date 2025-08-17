from typing import List, Self, Set, TypedDict, cast
from uuid import uuid4

import httpx
import scrapy.crawler
import scrapy.exceptions
import scrapy.signals

from betor.databases.redis import get_redis_client


class FlareSolverrSessionsCreateResponse(TypedDict):
    session: str


class FlareSolverrListSessionsResponse(TypedDict):
    sessions: List[str]


class FlareSolverrExtension:
    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler) -> Self:
        base_url = crawler.settings.get("FLARESOLVERR_BASE_URL")
        if not base_url:
            raise scrapy.exceptions.NotConfigured
        session_prefix = crawler.settings.get(
            "FLARESOLVERR_SESSION_PREFIX", "flaresolverr-extension:"
        )
        redis_locked_sessions_key = crawler.settings.get(
            "FLARESOLVERR_REDIS_LOCKED_SESSIONS_KEY", "flaresolverr:locked_sessions"
        )
        obj = cls(base_url, session_prefix, redis_locked_sessions_key)
        crawler.signals.connect(obj.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=scrapy.signals.spider_closed)
        return obj

    def __init__(
        self,
        base_url: str,
        session_prefix: str,
        redis_locked_sessions_key: str,
    ):
        self.redis_client = get_redis_client()
        self.base_url = base_url
        self.session_prefix = session_prefix
        self.redis_locked_sessions_key = redis_locked_sessions_key

    def spider_opened(self, spider: scrapy.Spider) -> None:
        self.redis_client.ping()
        spider.flaresolverr = self  # type: ignore[attr-defined]

    def spider_closed(self, spider: scrapy.Spider) -> None:
        self.redis_client.close()

    def get_available_sessions(self) -> Set[str]:
        response = httpx.post(
            f"{self.base_url}/v1",
            json={"cmd": "sessions.list"},
        )
        response.raise_for_status()
        data = cast(FlareSolverrListSessionsResponse, response.json())
        return set(
            [
                session
                for session in data["sessions"]
                if session.startswith(self.session_prefix)
            ]
        )

    def get_free_sessions(self) -> Set[str]:
        available_sessions = self.get_available_sessions()
        locked_sessions = cast(
            Set, self.redis_client.smembers(self.redis_locked_sessions_key)
        )
        return set(available_sessions - locked_sessions)

    def get_free_session(self) -> str:
        free_sessions = self.get_free_sessions()
        try:
            session = free_sessions.pop()
        except KeyError:
            session = self.create_session()
        self.redis_client.sadd(self.redis_locked_sessions_key, session)
        return session

    def create_session(self) -> str:
        response = httpx.post(
            f"{self.base_url}/v1",
            json={
                "cmd": "sessions.create",
                "session": f"{self.session_prefix}{uuid4()}",
            },
        )
        response.raise_for_status()
        data = cast(FlareSolverrSessionsCreateResponse, response.json())
        return data["session"]

    def free_session(self, session: str):
        self.redis_client.srem(self.redis_locked_sessions_key, session)
