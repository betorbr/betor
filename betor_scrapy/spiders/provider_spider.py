from typing import Optional

import scrapy

from betor.providers import Provider


class ProviderSpider:
    provider: Provider
    deep: int
    q: Optional[str]

    def __init__(self, *args, deep: str | int = 1, q: Optional[str] = None, **kwargs):
        super().__init__(*args, deep=int(deep), q=q, **kwargs)  # type: ignore

    def page_url(self, page_n: int) -> str:
        if self.q:
            return self.provider.get_search_url(self.q, page_n)
        return self.provider.get_page_url(page_n)

    async def start(self):
        for url in [self.page_url(page_n) for page_n in range(1, self.deep + 1)]:
            yield scrapy.Request(
                url,
                dont_filter=True,
                flags=["no-cache"],
                meta={"cf_clearance_domain": self.provider.cf_clearance_domain},
            )
