import base64
import binascii
import re
from urllib.parse import unquote, urlsplit

import scrapy
import scrapy.http
import torf
from scrapy.selector import Selector

from betor.providers import darkmahou
from betor_scrapy.loaders import ProviderLoader

from .provider_spider import ProviderSpider


def decode_magnet_link(href: str) -> str | None:
    """Accept direct magnets or one Base64 redirect, without fetching its target."""
    candidate = href.strip()
    try:
        if not candidate.startswith("magnet:?"):
            parsed = urlsplit(candidate)
            if parsed.scheme not in ("", "http", "https"):
                return None
            if not parsed.path.endswith("/redirect.php"):
                return None
            # Do not use parse_qs here: literal '+' is valid Base64, not a space.
            values = [
                unquote(value)
                for part in parsed.query.split("&")
                for key, separator, value in [part.partition("=")]
                if separator and unquote(key) == "url"
            ]
            if len(values) != 1 or not values[0]:
                return None
            encoded = values[0]
            encoded += "=" * (-len(encoded) % 4)
            candidate = (
                base64.b64decode(encoded, altchars=b"-_", validate=True)
                .decode("utf-8")
                .strip()
            )
        if not candidate.startswith("magnet:?"):
            return None
        torf.Magnet.from_string(candidate)
        return candidate
    except (ValueError, UnicodeError, binascii.Error, torf.MagnetError):
        return None


class DarkMahouSpider(ProviderSpider, scrapy.Spider):
    provider = darkmahou
    name = darkmahou.slug
    allowed_domains = darkmahou.domains

    def parse(self, response: scrapy.http.Response):
        assert isinstance(response, scrapy.http.TextResponse)
        feed = Selector(text=response.text, type="xml")
        if not feed.xpath("/rss/channel"):
            self.logger.warning("Expected a DarkMahou RSS feed at %s", response.url)
            return
        seen: set[str] = set()
        for entry in feed.xpath("/rss/channel/item"):
            link = entry.xpath("link/text()").get()
            if not link:
                continue
            url = response.urljoin(link.strip())
            parsed = urlsplit(url)
            if (
                parsed.scheme not in ("http", "https")
                or parsed.hostname not in self.allowed_domains
                or url in seen
            ):
                continue
            seen.add(url)
            yield scrapy.Request(
                url,
                callback=self.parse_item,
                cb_kwargs={"feed_title": entry.xpath("title/text()").get()},
                flags=["no-cache"],
            )

    def parse_item(self, response: scrapy.http.Response, feed_title: str | None = None):
        assert isinstance(response, scrapy.http.TextResponse)
        loader = ProviderLoader(self.provider, response=response)
        title = response.css("h1.entry-title").xpath("string(.)").get()
        loader.add_value("raw_title", title or feed_title)
        loader.add_value("title", title or feed_title)

        # Release year, not the WordPress publication/update timestamp.
        for field in response.css(".info-content .spe > span"):
            label = field.xpath("normalize-space(b)").get()
            if label == "Lançado:":
                value = field.xpath("string(.)").get(default="")
                match = re.search(r"\b(?:19|20)\d{2}\b", value)
                if match:
                    loader.add_value("year", match.group())
        loader.add_css("cast", ".info-content a.casts::text")
        loader.add_css(
            "imdb_id", ".info-content a[href*='imdb.com/title/']::attr(href)"
        )

        # Only download blocks; exclude comments, recommendations and ads.
        magnets: dict[str, str] = {}
        for href in response.css(".soraddl a::attr(href)").getall():
            magnet_uri = decode_magnet_link(href)
            if magnet_uri is None:
                continue
            # Different releases remain separate; duplicate wrappers collapse.
            magnet = torf.Magnet.from_string(magnet_uri)
            magnets.setdefault(magnet.xt.lower(), magnet_uri)
        if not magnets:
            self.logger.info("No supported magnets at %s", response.url)
            return
        loader.add_value("magnet_uris", list(magnets.values()))
        yield loader.load_item()
