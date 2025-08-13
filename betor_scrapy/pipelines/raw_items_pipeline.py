from betor.databases.mongodb import get_mongodb_client
from betor.services import InsertOrUpdateRawItemService
from betor_scrapy.items import ScrapyItem


class RawItemsPipeline:
    def open_spider(self, spider):
        self.mongodb_client = get_mongodb_client()
        self.insert_or_update_raw_item_service = InsertOrUpdateRawItemService(
            self.mongodb_client
        )

    def close_spider(self, spider):
        self.mongodb_client.close()

    async def process_item(self, item: ScrapyItem, spider):
        raw_item = item.to_raw_item()
        await self.insert_or_update_raw_item_service.insert_or_update(raw_item)
        return item
