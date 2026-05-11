import base64
from typing import TYPE_CHECKING, List, Optional
from urllib.parse import parse_qs, urlparse

import scrapy.http

from betor_scrapy.loaders import ProviderLoader

if TYPE_CHECKING:
    from scrapy.utils.log import SpiderLoggerAdapter


class UnlockSystemAdsMixin:
    PROTECTED_URLS_PREFIXES = [
        "https://www.systemads.org/get.php?id=",
        "https://superadsgo.xyz/get.php?id=",
        "https://superadsgo1.xyz/get.php?id=",
        "https://www.systemads.xyz/get.php?id=",
        "https://systemads.net/go.php?id=",
    ]

    @classmethod
    def get_allowed_domains(cls) -> List[str]:
        return [
            urlparse(protected_url_prefix).netloc
            for protected_url_prefix in cls.PROTECTED_URLS_PREFIXES
        ]

    @classmethod
    def unlock_protected_redirect_link(cls, redirect_url: str) -> str:
        parsed = urlparse(redirect_url)
        qs = parse_qs(parsed.query)
        id_values = qs.get("id")
        if not id_values:
            raise ValueError("id value not found")
        id_value = "".join(id_values)[::-1]
        try:
            return base64.b64decode(id_value).decode()
        except Exception as e:
            raise ValueError("can't decode base64 value") from e

    @classmethod
    def unlock_encrypted_protected_link(cls, response_content: str) -> str:
        redirect_url = None
        for line in response_content.splitlines():
            if "?id=" in line:
                start = line.find("https://")
                end = line.find('"', start)
                if start != -1 and end != -1:
                    redirect_url = line[start:end]
                    break
        if not redirect_url:
            raise ValueError("Redirect URL not found in response")
        return cls.unlock_protected_redirect_link(redirect_url)

    logger: "SpiderLoggerAdapter"

    def unlock_system_ads_magnet_uris(
        self, response: scrapy.http.Response, loader: ProviderLoader
    ):
        protected_urls = []
        for protected_url_prefix in self.PROTECTED_URLS_PREFIXES:
            protected_urls.extend(
                response.xpath(
                    f"//a[starts-with(@href, '{protected_url_prefix}')]/@href"
                ).getall()
            )
        if protected_urls:
            yield from self._next_unlock_system_ads_protected_url(
                None, loader, protected_urls
            )
        else:
            yield loader.load_item()

    def _next_unlock_system_ads_protected_url(
        self,
        response: Optional[scrapy.http.Response],
        loader: ProviderLoader,
        protected_urls: List[str],
    ):
        if response is not None:
            try:
                unlocked = self.unlock_encrypted_protected_link(response.text)
                loader.add_value("magnet_uris", unlocked)
            except ValueError:
                self.logger.debug("Can't not unlock URL: %s", response.url)
        if not protected_urls:
            yield loader.load_item()
            return
        next_protected_url = protected_urls.pop(0)
        try:
            unlocked = self.unlock_protected_redirect_link(next_protected_url)
            loader.add_value("magnet_uris", unlocked)
            yield from self._next_unlock_system_ads_protected_url(
                None, loader, protected_urls
            )
        except ValueError:
            yield scrapy.Request(
                url=next_protected_url,
                callback=self._next_unlock_system_ads_protected_url,
                cb_kwargs={"loader": loader, "protected_urls": protected_urls},
            )
