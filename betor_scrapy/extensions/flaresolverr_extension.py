import functools
from typing import Dict, List, Optional, Self, Set, TypedDict, cast
from uuid import uuid4

import httpx
import requests
import scrapy.crawler
import scrapy.exceptions
import scrapy.signals

from betor.databases.redis import get_redis_client


class FlareSolverrSessionsCreateResponse(TypedDict):
    session: str


class FlareSolverrListSessionsResponse(TypedDict):
    sessions: List[str]


class FlareSolverrSessionsExceeded(Exception):
    pass


class FlareSolverrExtension:
    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler) -> Self:
        base_url = crawler.settings.get("FLARESOLVERR_BASE_URL")
        if not base_url:
            raise scrapy.exceptions.NotConfigured
        session_prefix = crawler.settings.get(
            "FLARESOLVERR_SESSION_PREFIX", "flaresolverr-extension:"
        )
        redis_cf_clearance_key = crawler.settings.get(
            "FLARESOLVERR_REDIS_CF_CLEARANCE_KEY", "flaresolverr:cf_clearance:{domain}"
        )
        max_sessions = crawler.settings.get("FLARESOLVERR_MAX_SESSIONS", 3)
        obj = cls(
            base_url,
            session_prefix,
            redis_cf_clearance_key,
            max_sessions,
        )
        crawler.signals.connect(obj.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=scrapy.signals.spider_closed)
        return obj

    def __init__(
        self,
        base_url: str,
        session_prefix: str,
        redis_cf_clearance_key: str,
        max_sessions: int,
    ):
        self.redis_client = get_redis_client()
        self.base_url = base_url
        self.session_prefix = session_prefix
        self.redis_cf_clearance_key = redis_cf_clearance_key
        self.max_sessions = max_sessions

    def spider_opened(self, spider: scrapy.Spider) -> None:
        self.redis_client.ping()
        self.create_sessions()
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

    def create_session(self) -> str:
        if len(self.get_available_sessions()) >= self.max_sessions:
            raise FlareSolverrSessionsExceeded()
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

    def create_sessions(self):
        while len(self.get_available_sessions()) < self.max_sessions:
            self.create_session()

    def build_redis_cf_clearance_key(self, domain: str):
        return self.redis_cf_clearance_key.format(domain=domain)

    def add_cf_clearance(
        self, domain: str, value: str, user_agent: str, expire_at: Optional[int] = None
    ):
        redis_key = self.build_redis_cf_clearance_key(domain)
        self.redis_client.hset(redis_key, value, user_agent)
        if expire_at:
            self.redis_client.hexpireat(redis_key, expire_at, value)

    def remove_cf_clearance(self, domain: str, value: str):
        redis_key = self.build_redis_cf_clearance_key(domain)
        self.redis_client.hdel(redis_key, value)

    def cf_clearance_session_response_hook(
        self,
        response: requests.Response,
        domain: str,
        cf_clearance_value: str,
        **kwargs,
    ):
        if not response.ok:
            self.remove_cf_clearance(domain, cf_clearance_value)

    def get_cf_clearance_session(self, domain: str) -> Optional[requests.Session]:
        redis_key = self.build_redis_cf_clearance_key(domain)
        domain_values = cast(Dict[bytes, bytes], self.redis_client.hgetall(redis_key))
        for value, user_agent in domain_values.items():
            session = requests.Session()
            session.hooks["response"] = functools.partial(
                self.cf_clearance_session_response_hook,
                domain=domain,
                cf_clearance_value=value.decode(),
            )
            session.cookies.set("cf_clearance", value.decode())
            session.headers.update({"User-Agent": user_agent.decode()})
            return session
        return None
