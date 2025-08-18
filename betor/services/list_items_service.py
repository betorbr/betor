from typing import Dict, List, Optional

import motor.motor_asyncio
from bson.objectid import ObjectId

from betor.entities import Item
from betor.enums import ItemsSortEnum, ItemType
from betor.repositories import ItemsRepository
from betor.types import ApaginateParams, CursorSort

CURSOR_SORT_MAPPING: Dict[ItemsSortEnum, CursorSort] = {
    ItemsSortEnum.inserted_at_asc: ItemsRepository.INSERTED_AT_FIELD,
    ItemsSortEnum.inserted_at_desc: (
        ItemsRepository.INSERTED_AT_FIELD,
        -1,
    ),
    ItemsSortEnum.updated_at_asc: ItemsRepository.UPDATED_AT_FIELD,
    ItemsSortEnum.updated_at_desc: (
        ItemsRepository.UPDATED_AT_FIELD,
        -1,
    ),
}


class ListItemsService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    def apaginate_params(
        self,
        sort: ItemsSortEnum,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[str] = None,
        item_type: Optional[ItemType] = None,
        items_id: Optional[List[str]] = None,
    ) -> ApaginateParams[Item]:
        cursor_sort = CURSOR_SORT_MAPPING.get(sort)
        assert cursor_sort
        and_statements = []
        if imdb_id:
            and_statements.append({"imdb_id": imdb_id})
        if tmdb_id:
            and_statements.append({"tmdb_id": tmdb_id})
        if item_type:
            and_statements.append({"item_type": item_type})
        query_filter = (
            {
                **({"$and": and_statements} if and_statements else {}),
                **(
                    {"_id": {"$in": [ObjectId(item_id) for item_id in items_id]}}
                    if items_id is not None
                    else {}
                ),
            }
            if and_statements or items_id is not None
            else None
        )
        return (
            self.items_repository.collection,
            query_filter,
            cursor_sort,
            ItemsRepository.parse_results,
        )
