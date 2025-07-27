from typing import Any

import scrapy
import scrapy.crawler
import scrapy.http
import scrapy.signals


class BetorScrapySpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=scrapy.signals.spider_opened)
        return s

    def process_spider_input(
        self, response: scrapy.http.Response, spider: scrapy.Spider
    ):
        return None

    def process_spider_output(
        self, response: scrapy.http.Response, result: Any, spider: scrapy.Spider
    ):
        for i in result:
            yield i

    def process_spider_exception(
        self,
        response: scrapy.http.Response,
        exception: Exception,
        spider: scrapy.Spider,
    ):
        pass

    async def process_start(self, start):
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider: scrapy.Spider):
        spider.logger.info("Spider opened: %s" % spider.name)
