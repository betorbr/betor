from betor.databases.mongodb import get_mongodb_client
from betor.repositories import RawItemsRepository
from betor_scrapy.items import ScrapyItem


class ItemsRepositoryPipeline:
    def open_spider(self, spider):
        self.mongodb_client = get_mongodb_client()
        self.raw_items_repository = RawItemsRepository(self.mongodb_client)

    def close_spider(self, spider):
        self.mongodb_client.close()

    async def process_item(self, item: ScrapyItem, spider):
        await self.raw_items_repository.insert_or_update(item.to_raw_item())
        return item
