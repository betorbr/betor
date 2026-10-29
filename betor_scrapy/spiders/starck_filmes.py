import base64
import urllib.parse
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

    @classmethod
    def decode_base64_url(cls, base64_url: str) -> Optional[str]:
        if not base64_url:
            return None
        s = base64_url.replace("-", "+").replace("_", "/")
        s += "=" * ((4 - len(s) % 4) % 4)
        try:
            return base64.b64decode(s).decode("utf-8")
        except Exception:
            return None

    @classmethod
    def unlock_filmedl_link(cls, href: str) -> Optional[str]:
        try:
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            id_values = qs.get("id") or qs.get("xid")
            if not id_values:
                return None
            id_value = "".join(id_values)

            # Try reversal + base64 decode
            try:
                rev = id_value[::-1]
                s1 = rev.replace("-", "+").replace("_", "/")
                s1 += "=" * ((4 - len(s1) % 4) % 4)
                dec1 = base64.b64decode(s1).decode("utf-8")
                if "magnet:" in dec1:
                    return dec1
            except Exception:
                pass

            # Try unshuffle + base64 decode
            try:
                unsh = cls.unshuffle_string(id_value)
                s2 = unsh.replace("-", "+").replace("_", "/")
                s2 += "=" * ((4 - len(s2) % 4) % 4)
                dec2 = base64.b64decode(s2).decode("utf-8")
                if "magnet:" in dec2:
                    return dec2
            except Exception:
                pass

            # Try direct base64 decode / unshuffle
            dec3 = cls.decode_base64_url(id_value)
            if dec3:
                if "magnet:" in dec3:
                    return dec3
                try:
                    magnet_link = cls.unshuffle_string(dec3)
                    if "magnet:" in magnet_link:
                        return magnet_link
                except Exception:
                    pass
        except Exception:
            pass
        return None

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

        # Handle filmedl protected links (e.g. https://filmedl.com/sf_mone/?id=..., https://filmedl.com/?xid=...)
        for href in response.xpath(
            "//a[starts-with(@href, 'https://filmedl.com/')]/@href"
        ).getall():
            magnet_link = self.unlock_filmedl_link(href)
            if magnet_link:
                loader.add_value("magnet_uris", magnet_link)

        for shuffled_magnet_link in response.xpath("//@data-u").getall():
            try:
                magnet_link = StarckFilmesSpider.unshuffle_string(shuffled_magnet_link)
                if magnet_link:
                    loader.add_value("magnet_uris", magnet_link)
            except ValueError:
                self.logger.debug(
                    "Failed to unshuffle magnet link: %s", shuffled_magnet_link
                )
        yield loader.load_item()
