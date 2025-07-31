from typing import List
from urllib.parse import quote_plus, urlparse


class Provider:
    def __init__(
        self,
        slug: str,
        base_url: str,
        page_url: str,
        search_url: str,
        append_domains: List[str] = [],
    ):
        self.slug = slug
        self.base_url = base_url
        self.page_url = page_url
        self.search_url = search_url
        self.append_domains = append_domains

    @property
    def domains(self):
        base_url_parse_result = urlparse(self.base_url)
        return [base_url_parse_result.netloc, *self.append_domains]

    def get_page_url(self, page: int = 1) -> str:
        if page > 1:
            return self.page_url.format(base_url=self.base_url, page=page)
        return self.base_url

    def get_search_url(self, query: str) -> str:
        return self.search_url.format(base_url=self.base_url, qs=quote_plus(query))
