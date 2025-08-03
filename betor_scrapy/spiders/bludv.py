import scrapy
import scrapy.http

from betor.providers import bludv
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .provider_spider import ProviderSpider


class BludvSpider(ProviderSpider, scrapy.Spider):
    provider = bludv
    name = bludv.slug
    allowed_domains = bludv.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath(
            "//div[@class='post']//div[@class='content']//p//a[@class='more-link']"
        ):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath(
            "//div[@class='posts']//div[@class='post']//div[@class='title']//a/@href"
        ).getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(bludv, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "(//div[@class='post']//div[@class='content']//p)[strong]//text()"
            ).getall()
            if t.strip() not in ["", "\n", ":", ">>INFORMAÇÕES<<"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath(
            "raw_title", "//div[@class='post']//div[@class='title']//h1/text()"
        )
        loader.add_xpath("magnet_links", "//a[starts-with(@href, 'magnet')]/@href")
        loader.add_xpath(
            "imdb_id",
            "//div[@class='post']//a[starts-with(@href, 'https://www.imdb.com')]/@href",
        )
        yield loader.load_item()
