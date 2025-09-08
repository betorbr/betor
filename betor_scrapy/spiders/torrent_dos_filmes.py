import scrapy
import scrapy.http

from betor.providers import torrent_dos_filmes
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .provider_spider import ProviderSpider


class TorrentDosFilmesSpider(ProviderSpider, scrapy.Spider):
    provider = torrent_dos_filmes
    name = torrent_dos_filmes.slug
    allowed_domains = torrent_dos_filmes.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//main//div[@class='wp-pagenavi']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath(
            "//main//div[@class='post green']//a/@href"
        ).getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(torrent_dos_filmes, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "(//article//div[@class='content']//p)[1]//text()"
            ).getall()
            if t.strip() not in ["", "\n", ":", "»INFORMAÇÕES«"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//article//div[@class='title']//h1/text()")
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        loader.add_xpath(
            "imdb_id", "//article//a[starts-with(@href, 'https://www.imdb.com')]/@href"
        )
        yield loader.load_item()
