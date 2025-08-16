from typing import Optional

import scrapy

from betor.databases.mongodb import get_mongodb_client
from betor.databases.redis import get_redis_client
from betor.services import InsertOrUpdateRawItemService
from betor_scrapy.items import ScrapyItem


class RawItemsPipeline:
    def open_spider(self, spider):
        self.mongodb_client = get_mongodb_client()
        self.redis_client = get_redis_client()
        self.insert_or_update_raw_item_service = InsertOrUpdateRawItemService(
            self.mongodb_client, self.redis_client
        )

    def close_spider(self, spider):
        self.mongodb_client.close()
        self.redis_client.close()

    async def process_item(self, item: ScrapyItem, spider: scrapy.Spider):
        job_monitor_id: Optional[str] = getattr(spider, "job_monitor_id", None)
        job_index: Optional[str] = getattr(spider, "job_index", None)
        raw_item = item.to_raw_item()
        await self.insert_or_update_raw_item_service.insert_or_update(
            raw_item, job_monitor_id=job_monitor_id, job_index=job_index
        )
        return item
