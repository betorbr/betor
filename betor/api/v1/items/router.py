import pymongo
from fastapi import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.enum import ItemsSortEnum
from betor.repositories import ItemsRepository

from .schemas import ItemSchema

items_router = APIRouter()

CURSOR_SORT_MAPPING = {
    ItemsSortEnum.inserted_at_asc: ItemsRepository.INSERTED_AT_FIELD,
    ItemsSortEnum.inserted_at_desc: (
        ItemsRepository.INSERTED_AT_FIELD,
        pymongo.DESCENDING,
    ),
    ItemsSortEnum.updated_at_asc: ItemsRepository.UPDATED_AT_FIELD,
    ItemsSortEnum.updated_at_desc: (
        ItemsRepository.UPDATED_AT_FIELD,
        pymongo.DESCENDING,
    ),
}


@items_router.get("/")
async def list_items(
    request: BetorRequest, sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc
) -> Page[ItemSchema]:
    repository = ItemsRepository(request.app.mongodb_client)
    return await apaginate(
        repository.collection,
        sort=CURSOR_SORT_MAPPING.get(sort),
        transformer=ItemsRepository.parse_results,
    )
