import scrapy
import scrapy.http

from betor.providers import rede_torrent
from betor_scrapy.loaders import ProviderLoader
from betor_scrapy.utils import extract_fields

from .mixins import TitleJSONLDMixin
from .provider_spider import ProviderSpider


class RedeTorrentSpider(TitleJSONLDMixin, ProviderSpider, scrapy.Spider):
    provider = rede_torrent
    name = rede_torrent.slug
    allowed_domains = rede_torrent.domains

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//a[@class='text-decoration-none cover-link']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath(
            "//a[@class='text-decoration-none cover-link']/@href"
        ).getall():
            yield scrapy.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(rede_torrent, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "//div[@class='specs-grid-premium']/descendant-or-self::*/text()"
            ).getall()
            if t.strip() not in ["", "\n", ":"]
        ]
        for field, value in extract_fields(informacoes_text):
            loader.add_value(field, value)
        loader.add_xpath("raw_title", "//h1//text()")
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        title_data = self.extract_title_json_ld(response)
        if title_data:
            same_as = title_data.get("sameAs")
            if same_as:
                loader.add_value("imdb_id", same_as)
            name = title_data.get("name")
            if name:
                loader.add_value("translated_title", name)
            year = title_data.get("copyrightYear")
            if year:
                loader.add_value("year", year)
        yield loader.load_item()
