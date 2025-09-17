from fastapi import APIRouter
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate_aggregate

from betor.api.fast_api import BetorRequest
from betor.entities import CatalogItem
from betor.enums import CatalogItemsSortEnum
from betor.services import CatalogService

catalog_router = APIRouter()


@catalog_router.get("/")
async def catalog(
    request: BetorRequest,
    sort: CatalogItemsSortEnum = CatalogItemsSortEnum.last_updated_desc,
) -> Page[CatalogItem]:
    service = CatalogService(request.app.mongodb_client)
    collection, aggregate_pipeline, transformer = service.apaginate_aggregate_params(
        sort
    )
    return await apaginate_aggregate(
        collection,
        aggregate_pipeline,
        transformer=transformer,
    )
