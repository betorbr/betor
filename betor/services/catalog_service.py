from typing import Dict

import motor.motor_asyncio

from betor.entities import CatalogItem
from betor.enums import CatalogItemsSortEnum
from betor.repositories import CatalogItemsRepository
from betor.types import ApaginateAggregateParams

SORT_VALUE_MAPPING: Dict[CatalogItemsSortEnum, Dict[str, int]] = {
    CatalogItemsSortEnum.last_updated_asc: {"last_updated": 1},
    CatalogItemsSortEnum.last_updated_desc: {"last_updated": -1},
}


class CatalogService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.catalog_items_repository = CatalogItemsRepository(mongodb_client)

    def apaginate_aggregate_params(
        self, sort: CatalogItemsSortEnum
    ) -> ApaginateAggregateParams[CatalogItem]:
        sort_value = SORT_VALUE_MAPPING.get(sort)
        assert sort_value
        return (
            self.catalog_items_repository.collection,
            self.catalog_items_repository.aggr_pipeline + [{"$sort": sort_value}],
            CatalogItemsRepository.parse_results,
        )
