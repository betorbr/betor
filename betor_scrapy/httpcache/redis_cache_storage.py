import pickle
from typing import List, Optional, TypedDict, cast

import redis.exceptions
import scrapy
import scrapy.http
import scrapy.responsetypes
import scrapy.settings

from betor.databases.redis import get_redis_client


class _ResponseData(TypedDict):
    url: str
    headers: dict
    status: int
    body: bytes
    flags: List[str]


class RedisCacheStorage:
    redis_available = False

    def __init__(self, settings: scrapy.settings.Settings):
        self.redis_client = get_redis_client()
        self.expiration_secs = settings.getint("HTTPCACHE_EXPIRATION_SECS")

    def open_spider(self, spider: scrapy.Spider):
        try:
            self.redis_client.ping()
            self.redis_available = True
            spider.logger.info(
                f"[RedisCacheStorage] Redis available -> {self.expiration_secs=}"
            )
        except redis.exceptions.ConnectionError:
            spider.logger.warning("[RedisCacheStorage] Redis not available!")
            self.redis_available = False

    def close_spider(self, spider: scrapy.Spider):
        pass

    def _get_request_key(self, spider: scrapy.Spider, request: scrapy.Request):
        assert spider.crawler.request_fingerprinter
        return spider.crawler.request_fingerprinter.fingerprint(request).hex()

    def store_response(
        self,
        spider: scrapy.Spider,
        request: scrapy.Request,
        response: scrapy.http.Response,
    ):
        if not self.redis_available:
            return
        key = self._get_request_key(spider, request)
        response_data = _ResponseData(
            url=response.url,
            headers=dict(response.headers),
            status=response.status,
            body=response.body,
            flags=response.flags,
        )
        data = pickle.dumps(response_data, protocol=pickle.HIGHEST_PROTOCOL)
        self.redis_client.set(key, data, ex=self.expiration_secs)

    def retrieve_response(
        self, spider: scrapy.Spider, request: scrapy.Request
    ) -> Optional[scrapy.http.Response]:
        if not self.redis_available:
            return None
        key = self._get_request_key(spider, request)
        data = cast(Optional[bytes], self.redis_client.get(key))
        if data is None:
            return None
        response_data = cast(_ResponseData, pickle.loads(data))
        headers = scrapy.http.Headers(response_data["headers"])
        respcls = scrapy.responsetypes.responsetypes.from_args(
            headers=headers, url=response_data["url"], body=response_data["body"]
        )
        return respcls(
            url=response_data["url"],
            headers=headers,
            status=response_data["status"],
            body=response_data["body"],
            flags=response_data["flags"],
        )
