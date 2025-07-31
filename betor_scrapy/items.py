import scrapy


class ProviderItem(scrapy.Item):
    provider_slug = scrapy.Field()
    provider_url = scrapy.Field()
    title = scrapy.Field()
    translated_title = scrapy.Field()
    raw_title = scrapy.Field()
    year = scrapy.Field(serializer=int)
    qualitys = scrapy.Field()
