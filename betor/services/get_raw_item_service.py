from typing import Optional

import motor.motor_asyncio

from betor.entities import RawItem
from betor.repositories import RawItemsRepository


class GetRawItemService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.raw_items_repository = RawItemsRepository(mongodb_client)

    async def retrieve(self, raw_item_id: str) -> Optional[RawItem]:
        return await self.raw_items_repository.get_by_id(raw_item_id)
