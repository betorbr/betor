from typing import Optional

from fastapi import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.enums import ItemsSortEnum, ItemType
from betor.services import ListItemsService

from .schemas import ItemSchema

items_router = APIRouter()


@items_router.get("/")
async def list_items(
    request: BetorRequest,
    sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc,
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    item_type: Optional[ItemType] = None,
) -> Page[ItemSchema]:
    service = ListItemsService(request.app.mongodb_client)
    collection, query_filter, cursor_sort, transformer = service.apaginate_params(
        sort, imdb_id=imdb_id, tmdb_id=tmdb_id, item_type=item_type
    )
    return await apaginate(
        collection,
        query_filter=query_filter,
        sort=cursor_sort,
        transformer=transformer,
    )
