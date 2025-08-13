from typing import List, Optional
from urllib.parse import quote_plus, urlparse


class Provider:
    def __init__(
        self,
        slug: str,
        base_url: str,
        page_url: str,
        search_url: str,
        search_page_url: Optional[str] = None,
        append_domains: List[str] = [],
    ):
        self.slug = slug
        self.base_url = base_url
        self.page_url = page_url
        self.search_url = search_url
        self.search_page_url = search_page_url
        self.append_domains = append_domains

    @property
    def domains(self):
        base_url_parse_result = urlparse(self.base_url)
        return [base_url_parse_result.netloc, *self.append_domains]

    def get_page_url(self, page: int = 1) -> str:
        if page > 1:
            return self.page_url.format(base_url=self.base_url, page=page)
        return self.base_url

    def get_search_url(self, query: str, page: int = 1) -> str:
        if self.search_page_url and page > 1:
            return self.search_page_url.format(
                base_url=self.base_url, qs=quote_plus(query), page=page
            )
        return self.search_url.format(base_url=self.base_url, qs=quote_plus(query))
