from urllib.parse import urlencode

from .provider import Provider


class DarkMahouProvider(Provider):
    def get_page_url(self, page: int = 1) -> str:
        url = f"{self.base_url}/feed/"
        return f"{url}?{urlencode({'paged': page})}" if page > 1 else url

    def get_search_url(self, query: str, page: int = 1) -> str:
        params: dict[str, str | int] = {"s": query}
        if page > 1:
            params["paged"] = page
        return f"{self.base_url}/feed/?{urlencode(params)}"


darkmahou = DarkMahouProvider(
    "darkmahou",
    "https://darkmahou.io",
    "{base_url}/feed/?paged={page}",
    "{base_url}/feed/?s={qs}",
    "{base_url}/feed/?s={qs}&paged={page}",
)
