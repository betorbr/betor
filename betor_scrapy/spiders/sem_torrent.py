import scrapy
import scrapy.http

from betor.providers import sem_torrent
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .provider_spider import ProviderSpider


class SemTorrentSpider(ProviderSpider, scrapy.Spider):
    provider = sem_torrent
    name = sem_torrent.slug
    allowed_domains = sem_torrent.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//div[@class='capa_lista']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath(
            "//div[@class='capa_lista']//a[1]/@href"
        ).getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(sem_torrent, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath("(//div[@id='informacoes']//p)[1]//text()").getall()
            if t.strip() not in ["", "\n"]
        ]
        print(informacoes_text)
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//h1/text()")
        loader.add_xpath("title", "//h2//a//@title")
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        loader.add_xpath(
            "imdb_id", "//a[starts-with(@href, 'https://www.opensubtitles.org')]/@href"
        )
        loader.add_xpath(
            "imdb_id", "//a[starts-with(@href, 'https://yifysubtitles.ch')]/@href"
        )
        yield loader.load_item()
