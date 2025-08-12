from betor.celery import process_raw_item
from betor_scrapy.items import ScrapyItem


class DispatchProcessRawItemPipeline:
    async def process_item(self, item: ScrapyItem, spider):
        process_raw_item.delay(item["provider_slug"], item["provider_url"])
        return item
