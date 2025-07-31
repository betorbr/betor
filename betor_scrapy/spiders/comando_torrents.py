import itertools
from typing import Optional

import scrapy
import scrapy.http
from slugify import slugify

from betor.providers import comando_torrents
from betor_scrapy.items import ProviderItem
from betor_scrapy.loaders import ProviderLoader

FIELD_TOKENS = {
    "translated_title": ["titulo-traduzido"],
    "title": ["titulo-original"],
    "imdb": ["imdb"],
    "year": ["lancamento"],
    "quality": ["qualidade"],
    "languages": ["idioma"],
    "genres": ["genero"],
    "format": ["formato"],
    "subtitles": ["legenda"],
    "size": ["tamanho"],
    "duration": ["duracao"],
    "audio-quality": ["qualidade-do-audio"],
    "video-quality": ["qualidade-de-video"],
    "server": ["servidor"],
}
ALL_FIELD_TOKENS_VALUES = list(itertools.chain(*FIELD_TOKENS.values()))


class ComandoTorrentsSpider(scrapy.Spider):
    name = comando_torrents.slug
    allowed_domains = comando_torrents.domains
    start_urls = [comando_torrents.get_page_url()]

    def parse(self, response: scrapy.http.Response):
        if response.xpath("//article//div[@itemprop='text']//p//a[@class='more-link']"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_item(response)

    def parse_page(self, response: scrapy.http.Response):
        for item_url in response.xpath("//article//header//h2//a/@href").getall():
            yield scrapy.http.Request(item_url)

    def parse_item(self, response: scrapy.http.Response):
        loader = ProviderLoader(comando_torrents, response=response)
        informacoes_text = [
            t.strip()
            for t in response.xpath(
                "(//article//div[@itemprop='text']//p)[span]//text()"
            ).getall()
            if t.strip() not in ["", "\n", ":", "»INFORMAÇÕES«"]
        ]
        current_field: Optional[str] = None
        for i, token_value in enumerate([slugify(t) for t in informacoes_text]):
            if token_value in ALL_FIELD_TOKENS_VALUES:
                current_field = next(
                    k for k, v in FIELD_TOKENS.items() if token_value in v
                )
                continue
            if current_field and current_field in ProviderItem.fields.keys():
                loader.add_value(current_field, informacoes_text[i])
        loader.add_xpath("raw_title", "//article//header//h1//a/text()")
        yield loader.load_item()
