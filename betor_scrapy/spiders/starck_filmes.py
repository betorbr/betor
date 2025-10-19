import scrapy
import scrapy.http

from betor.providers import starck_filmes
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .provider_spider import ProviderSpider


class StarckFilmesSpider(ProviderSpider, scrapy.Spider):
    provider = starck_filmes
    name = starck_filmes.slug
    allowed_domains = starck_filmes.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath(
            "//section[@class='container']//div[@class='home post-catalog']"
        ):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath(
            "//section[@class='container']//div[@class='home post-catalog']//div[@class='item']//div[@class='sub-item']//a[@title]/@href"
        ).getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(starck_filmes, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "//div[@class='post-description']//p//text()"
            ).getall()
            if t.strip() not in ["", "\n", ":"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//div[@class='main-title']//h1//text()")
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        yield loader.load_item()
