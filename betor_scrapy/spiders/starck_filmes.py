from typing import List, Optional

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

    @classmethod
    def unshuffle_string(cls, shuffled: str) -> str:
        length = len(shuffled)
        original: List[Optional[str]] = [None] * length
        used = [False] * length
        step = 3
        index = 0
        for i in range(length):
            while used[index]:
                index = (index + 1) % length
            used[index] = True
            original[i] = shuffled[index]
            index = (index + step) % length
        return "".join(map(str, original))

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
        for shuffled_magnet_link in response.xpath("//@data-u").getall():
            try:
                magnet_link = StarckFilmesSpider.unshuffle_string(shuffled_magnet_link)
                loader.add_value("magnet_uris", magnet_link)
            except ValueError:
                self.logger.debug(
                    "Failed to unshuffle magnet link: %s", shuffled_magnet_link
                )
        yield loader.load_item()
