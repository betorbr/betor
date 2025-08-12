from betor.celery import celery_app
from betor_scrapy.items import ScrapyItem


class DispatchProcessRawItemPipeline:
    async def process_item(self, item: ScrapyItem, spider):
        celery_app.signature("process_raw_item").delay(
            item["provider_slug"], item["provider_url"]
        )
        return item
