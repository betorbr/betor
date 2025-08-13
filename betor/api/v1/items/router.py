from fastapi import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.repositories import ItemsRepository

from .enum import ItemsSortEnum
from .schemas import ItemSchema

items_router = APIRouter()


@items_router.get("/")
async def list_items(
    request: BetorRequest, sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc
) -> Page[ItemSchema]:
    repository = ItemsRepository(request.app.mongodb_client)
    return await apaginate(
        repository.collection,
        sort=sort,
        transformer=ItemsRepository.parse_results,
    )
