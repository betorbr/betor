import pickle
from typing import Optional

import redis.exceptions
import scrapy
import scrapy.http
import scrapy.responsetypes
import scrapy.settings

from betor.databases.redis import get_redis_client


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
        data = pickle.dumps(
            {
                "url": response.url,
                "headers": dict(response.headers),
                "status": response.status,
                "body": response.body,
                "flags": response.flags,
            },
            protocol=pickle.HIGHEST_PROTOCOL,
        )
        self.redis_client.set(key, data, ex=self.expiration_secs)

    def retrieve_response(
        self, spider: scrapy.Spider, request: scrapy.Request
    ) -> Optional[scrapy.http.Response]:
        if not self.redis_available:
            return None
        key = self._get_request_key(spider, request)
        data = self.redis_client.get(key)
        if data is None:
            return None
        data = pickle.loads(data)
        url = data["url"]
        headers = scrapy.http.Headers(data["headers"])
        status = data["status"]
        body = data["body"]
        flags = data["flags"]
        respcls = scrapy.responsetypes.responsetypes.from_args(
            headers=headers, url=url, body=body
        )
        return respcls(url=url, headers=headers, status=status, body=body, flags=flags)
