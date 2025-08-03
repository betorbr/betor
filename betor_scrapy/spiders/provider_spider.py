import scrapy

from betor.providers import Provider


class ProviderSpider:
    provider: Provider

    def __init__(self, *args, deep: str | int = 1, **kwargs):
        super().__init__(*args, deep=int(deep), **kwargs)  # type: ignore

    def start_requests(self):
        for url in [
            self.provider.get_page_url(page_n) for page_n in range(1, self.deep + 1)
        ]:
            yield scrapy.Request(url, dont_filter=True, flags=["no-cache"])
