import scrapy

from betor.entities import RawItem


class ScrapyItem(scrapy.Item):
    provider_slug = scrapy.Field()
    provider_url = scrapy.Field()
    title = scrapy.Field()
    translated_title = scrapy.Field()
    raw_title = scrapy.Field()
    year = scrapy.Field(serializer=int)
    qualitys = scrapy.Field()
    languages = scrapy.Field()
    magnet_uris = scrapy.Field()
    imdb_id = scrapy.Field()
    tmdb_id = scrapy.Field()

    def to_raw_item(self) -> RawItem:
        provider_slug = self.get("provider_slug")
        provider_url = self.get("provider_url")
        assert (
            provider_slug and provider_url
        ), f"Required {provider_slug=} {provider_url=}"
        return {
            "id": None,
            "hash": None,
            "inserted_at": None,
            "updated_at": None,
            "provider_slug": provider_slug,
            "provider_url": provider_url,
            "imdb_id": self.get("imdb_id"),
            "tmdb_id": self.get("tmdb_id"),
            "magnet_uris": self.get("magnet_uris", []),
            "languages": list(self.get("languages", set())),
            "qualitys": list(self.get("qualitys", set())),
            "title": self.get("title"),
            "translated_title": self.get("translated_title"),
            "raw_title": self.get("raw_title"),
            "year": self.get("year"),
        }
