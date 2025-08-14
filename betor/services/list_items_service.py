from typing import Callable, Dict, Sequence, Tuple, TypeAlias, Union

import motor.motor_asyncio

from betor.entities import Item
from betor.enums import ItemsSortEnum
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

    def apaginate_params(self, sort: ItemsSortEnum) -> Tuple[
        motor.motor_asyncio.AsyncIOMotorCollection,
        CursorSort,
        Callable[[Sequence[Dict]], Sequence[Item]],
    ]:
        cursor_sort = CURSOR_SORT_MAPPING.get(sort)
        assert cursor_sort
        return (
            self.items_repository.collection,
            cursor_sort,
            ItemsRepository.parse_results,
        )
