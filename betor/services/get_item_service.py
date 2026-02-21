from typing import Optional

import motor.motor_asyncio

from betor.entities import Item
from betor.repositories import ItemsRepository


class GetItemService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def retrieve(self, item_id: str) -> Optional[Item]:
        return await self.items_repository.get_by_id(item_id)
