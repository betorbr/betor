import base64
from urllib.parse import parse_qs, urlparse

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

    @classmethod
    def unlock_protected_link(cls, url: str) -> str:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        id_values = qs.get("id")
        if not id_values:
            raise ValueError("id value not found")
        id_value = "".join(id_values)[::-1]
        try:
            return base64.b64decode(id_value).decode()
        except Exception as e:
            raise ValueError("can't decode base64 value") from e

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
            yield scrapy.Request(
                item_url,
                meta={"cf_clearance_domain": self.provider.cf_clearance_domain},
            )

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
        loader.add_xpath("magnet_uris", "//a[starts-with(@href, 'magnet')]/@href")
        loader.add_xpath(
            "imdb_id",
            "//div[@class='post']//a[starts-with(@href, 'https://www.imdb.com')]/@href",
        )
        for protected_url in response.xpath(
            "//a[starts-with(@href, 'https://www.systemads.org/get.php?id=')]/@href"
        ).getall():
            try:
                unlocked = BludvSpider.unlock_protected_link(protected_url)
                loader.add_value("magnet_uris", unlocked)
            except ValueError:
                self.logger.debug("Can't not unlock URL: %s", protected_url)
        yield loader.load_item()
