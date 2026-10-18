import scrapy
import scrapy.http

from betor.providers import hdrtorrents
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .mixins import TitleJSONLDMixin
from .provider_spider import ProviderSpider


class HDRTorrentsSpider(TitleJSONLDMixin, ProviderSpider, scrapy.Spider):
    provider = hdrtorrents
    name = hdrtorrents.slug
    allowed_domains = hdrtorrents.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//a[@class='media-card-link']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath("//a[@class='media-card-link']/@href").getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(hdrtorrents, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "//dl[@class='item-specs']/descendant-or-self::*/text()"
            ).getall()
            if t.strip() not in ["", "\n", ":"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//h1[@class='item-h1']/text()")
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        title_data = self.extract_title_json_ld(response)
        if title_data:
            if name := title_data.get("name"):
                loader.add_value("translated_title", name)
            if alternateName := title_data.get("alternateName"):
                loader.add_value("title", alternateName)
            if date_published := title_data.get("datePublished"):
                loader.add_value("year", date_published[:4])
        yield loader.load_item()
