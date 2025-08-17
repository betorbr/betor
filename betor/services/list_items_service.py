from typing import Callable, Dict, Optional, Sequence, Tuple, TypeAlias, Union

import motor.motor_asyncio

from betor.entities import Item
from betor.enums import ItemsSortEnum, ItemType
from betor.repositories import ItemsRepository

CursorSort: TypeAlias = Union[str, Tuple[str, int]]

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
        imdb_id: Optional[str],
        tmdb_id: Optional[str],
        item_type: Optional[ItemType],
    ) -> Tuple[
        motor.motor_asyncio.AsyncIOMotorCollection,
        Optional[Dict],
        CursorSort,
        Callable[[Sequence[Dict]], Sequence[Item]],
    ]:
        cursor_sort = CURSOR_SORT_MAPPING.get(sort)
        assert cursor_sort
        and_statements = []
        if imdb_id:
            and_statements.append({"imdb_id": imdb_id})
        if tmdb_id:
            and_statements.append({"tmdb_id": tmdb_id})
        if item_type:
            and_statements.append({"item_type": item_type})
        return (
            self.items_repository.collection,
            {"$and": and_statements} if and_statements else None,
            cursor_sort,
            ItemsRepository.parse_results,
        )
