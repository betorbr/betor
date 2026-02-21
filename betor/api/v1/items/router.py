from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.entities import Item
from betor.enums import ItemsSortEnum, ItemType
from betor.services import GetItemService, ListItemsService

from .schemas import ItemSchema

items_router = APIRouter()


@items_router.get("/")
async def list_items(
    request: BetorRequest,
    sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc,
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    item_type: Annotated[Optional[List[ItemType]], Query()] = None,
    season: Annotated[Optional[List[int]], Query()] = None,
    episode: Annotated[Optional[List[int]], Query()] = None,
) -> Page[ItemSchema]:
    service = ListItemsService(request.app.mongodb_client)
    collection, query_filter, cursor_sort, transformer = service.apaginate_params(
        sort,
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        item_types=item_type,
        seasons=season,
        episodes=episode,
    )
    return await apaginate(
        collection,
        query_filter=query_filter,
        sort=cursor_sort,
        transformer=transformer,
    )


@items_router.get("/{item_id}", response_model=ItemSchema)
async def get_item(request: BetorRequest, item_id: str) -> Item:
    service = GetItemService(request.app.mongodb_client)
    item = await service.retrieve(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
