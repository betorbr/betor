import scrapy
import scrapy.http

from betor.providers import comando_torrents
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .provider_spider import ProviderSpider


class ComandoTorrentsSpider(ProviderSpider, scrapy.Spider):
    provider = comando_torrents
    name = comando_torrents.slug
    allowed_domains = comando_torrents.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//article//div[@itemprop='text']//p//a[@class='more-link']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath("//article//header//h2//a/@href").getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(comando_torrents, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "(//article//div[@itemprop='text']//p)[span]//text()"
            ).getall()
            if t.strip() not in ["", "\n", ":", "»INFORMAÇÕES«"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//article//header//h1//a/text()")
        loader.add_xpath("magnet_links", "//a[starts-with(@href, 'magnet')]/@href")
        loader.add_xpath(
            "imdb_id", "//article//a[starts-with(@href, 'https://www.imdb.com')]/@href"
        )
        yield loader.load_item()
