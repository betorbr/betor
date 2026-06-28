from typing import Optional

import motor.motor_asyncio

from betor.entities import RawItem
from betor.enums import RawItemsSortEnum
from betor.repositories import RawItemsRepository
from betor.types import ApaginateParams


class ListRawItemsService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.raw_items_repository = RawItemsRepository(mongodb_client)

    def apaginate_params(
        self,
        sort: RawItemsSortEnum,
        provider_slug: Optional[str] = None,
        provider_url: Optional[str] = None,
    ) -> ApaginateParams[RawItem]:
        return self.raw_items_repository.apaginate_params(
            sort,
            provider_slug=provider_slug,
            provider_url=provider_url,
        )
