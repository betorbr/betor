from fastapi import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.repositories import ItemsRepository

from .schemas import ItemSchema

items_router = APIRouter()


@items_router.get("/")
async def list_items(request: BetorRequest) -> Page[ItemSchema]:
    repository = ItemsRepository(request.app.mongodb_client)
    return await apaginate(
        repository.collection,
        sort=f"-{ItemsRepository.INSERTED_AT_FIELD}",
        transformer=ItemsRepository.parse_results,
    )
