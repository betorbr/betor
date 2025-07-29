from abc import ABCMeta, abstractmethod
from typing import Iterator

import scrapy.http


class ProviderBase(metaclass=ABCMeta):
    base_url: str
    page_url: str

    def get_page_url(self, page: int = 1) -> str:
        if page > 1:
            return self.page_url.format(base_url=self.base_url, page=page)
        return self.base_url

    @abstractmethod
    def parse_page(self, response: scrapy.http.Response) -> Iterator[str]: ...

    @abstractmethod
    def parse_item(self, response: scrapy.http.Response) -> Iterator[dict]: ...
