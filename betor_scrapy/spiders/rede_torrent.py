import scrapy
import scrapy.http

from betor.providers import rede_torrent
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .provider_spider import ProviderSpider


class RedeTorrentSpider(ProviderSpider, scrapy.Spider):
    provider = rede_torrent
    name = rede_torrent.slug
    allowed_domains = rede_torrent.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//div[@class='capas_pequenas']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath(
            "//div[@class='capas_pequenas']//div[@class='capa_lista']//a[@title]/@href"
        ).getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(rede_torrent, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath("//div[@id='informacoes']//p//text()").getall()
            if t.strip() not in ["", "\n", ":"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//h1[@itemprop='headline']//text()")
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        yield loader.load_item()
