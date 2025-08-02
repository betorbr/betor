from betor.databases.mongodb import get_mongodb_client
from betor.repositories import ItemsRepository
from betor_scrapy.items import ScrapyItem


class ItemsRepositoryPipeline:
    def open_spider(self, spider):
        self.mongodb_client = get_mongodb_client()
        self.items_repository = ItemsRepository(self.mongodb_client)

    def close_spider(self, spider):
        self.mongodb_client.close()

    async def process_item(self, item: ScrapyItem, spider):
        await self.items_repository.insert_or_update_item(item.to_item())
        return item
