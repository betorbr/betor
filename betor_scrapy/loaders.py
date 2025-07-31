from typing import Optional

import scrapy.http
import scrapy.loader
from itemloaders.processors import MapCompose, TakeFirst

from betor.providers.provider import Provider
from betor_scrapy.items import ProviderItem

from .processors import Title


class ProviderLoader(scrapy.loader.ItemLoader):
    default_item_class = ProviderItem
    default_output_processor = TakeFirst()

    title_out = Title()
    translated_title_out = Title()
    raw_title_out = Title()
    year_in = MapCompose(int)

    def __init__(
        self,
        provider: Provider,
        item=None,
        selector=None,
        response: Optional[scrapy.http.Response] = None,
        parent=None,
        **context,
    ):
        super().__init__(item, selector, response, parent, **context)
        self.add_value("provider_slug", provider.slug)
        if response:
            self.add_value("provider_url", response.url)
