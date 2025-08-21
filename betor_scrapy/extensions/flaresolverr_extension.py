import functools
from typing import Dict, List, Optional, Self, Set, Tuple, TypedDict, cast
from uuid import uuid4

import httpx
import redis.lock
import requests
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
        redis_lock_session_key = crawler.settings.get(
            "FLARESOLVERR_REDIS_LOCK_SESSION_KEY", "flaresolverr:lock_session:{session}"
        )
        redis_cf_clearance_key = crawler.settings.get(
            "FLARESOLVERR_REDIS_CF_CLEARANCE_KEY", "flaresolverr:cf_clearance:{domain}"
        )
        obj = cls(
            base_url,
            session_prefix,
            redis_lock_session_key,
            redis_cf_clearance_key,
        )
        crawler.signals.connect(obj.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=scrapy.signals.spider_closed)
        return obj

    def __init__(
        self,
        base_url: str,
        session_prefix: str,
        redis_lock_session_key: str,
        redis_cf_clearance_key: str,
    ):
        self.redis_client = get_redis_client()
        self.base_url = base_url
        self.session_prefix = session_prefix
        self.redis_lock_session_key = redis_lock_session_key
        self.redis_cf_clearance_key = redis_cf_clearance_key

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

    def is_free_session(self, session: str) -> bool:
        lock: redis.lock.Lock = self.redis_client.lock(
            self.redis_lock_session_key.format(session=session),
        )
        return not lock.locked()

    def get_free_sessions(self) -> Set[str]:
        available_sessions = self.get_available_sessions()
        return set(
            [session for session in available_sessions if self.is_free_session(session)]
        )

    def get_free_session(self) -> Tuple[str, redis.lock.Lock]:
        free_sessions = self.get_free_sessions()
        try:
            session = free_sessions.pop()
        except KeyError:
            session = self.create_session()
        lock: redis.lock.Lock = self.redis_client.lock(
            self.redis_lock_session_key.format(session=session),
        )
        lock.acquire(blocking=True)
        return session, lock

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

    def free_session(self, lock: redis.lock.Lock):
        lock.release()

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
