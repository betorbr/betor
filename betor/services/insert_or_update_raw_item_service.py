import motor.motor_asyncio

from betor.celery.app import celery_app
from betor.repositories import RawItemsRepository
from betor.types.raw_item import RawItem


class InsertOrUpdateRawItemService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.raw_items_repository = RawItemsRepository(mongodb_client)

    async def insert_or_update(self, raw_item: RawItem):
        await self.raw_items_repository.insert_or_update(raw_item)
        celery_app.signature("process_raw_item").delay(
            raw_item["provider_slug"], raw_item["provider_url"]
        )
