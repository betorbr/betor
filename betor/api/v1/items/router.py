from fastapi import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.enums import ItemsSortEnum
from betor.services import ListItemsService

from .schemas import ItemSchema

items_router = APIRouter()


@items_router.get("/")
async def list_items(
    request: BetorRequest, sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc
) -> Page[ItemSchema]:
    service = ListItemsService(request.app.mongodb_client)
    collection, cursor_sort, transformer = service.apaginate_params(sort)
    return await apaginate(
        collection,
        sort=cursor_sort,
        transformer=transformer,
    )
