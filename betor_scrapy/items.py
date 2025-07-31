import scrapy
import scrapy.item


class ProviderItem(scrapy.Item):
    provider_slug = scrapy.item.Field()
    provider_url = scrapy.item.Field()
    title = scrapy.item.Field()
    translated_title = scrapy.item.Field()
    raw_title = scrapy.item.Field()
