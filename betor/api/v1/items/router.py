import motor.motor_asyncio
from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.databases.mongodb import get_mongodb_client
from betor.repositories import ItemsRepository

from .schemas import ItemSchema

items_router = APIRouter()


@items_router.get("/")
async def list_items(
    mongodb_client: motor.motor_asyncio.AsyncIOMotorClient = Depends(
        get_mongodb_client
    ),
) -> Page[ItemSchema]:
    repository = ItemsRepository(mongodb_client)
    return await apaginate(
        repository.collection,
        sort=f"-{ItemsRepository.INSERTED_AT_FIELD}",
        transformer=ItemsRepository.parse_results,
    )
