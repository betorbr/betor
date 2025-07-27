import scrapy.crawler
import scrapy.http
import scrapy.signals


class BetorScrapyDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=scrapy.signals.spider_opened)
        return s

    def process_request(self, request: scrapy.http.Request, spider: scrapy.Spider):
        return None

    def process_response(
        self,
        request: scrapy.http.Request,
        response: scrapy.http.Response,
        spider: scrapy.Spider,
    ):
        return response

    def process_exception(
        self, request: scrapy.http.Request, exception: Exception, spider: scrapy.Spider
    ):
        pass

    def spider_opened(self, spider: scrapy.Spider):
        spider.logger.info("Spider opened: %s" % spider.name)
