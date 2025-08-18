from typing import Annotated, List, Optional

from fastapi import APIRouter, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.api.v1.items.schemas import ItemSchema
from betor.enums import ItemsSortEnum
from betor.providers import ProviderSlug
from betor.services import SearchService

search_router = APIRouter()


@search_router.get("/")
async def search(
    request: BetorRequest,
    q: str,
    sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc,
    deep: int = 3,
    scrape_timeout: int = 30,
    process_raw_item_timeout: int = 30,
    provider: Annotated[Optional[List[ProviderSlug]], Query()] = None,
) -> Page[ItemSchema]:
    service = SearchService(request.app.mongodb_client, request.app.redis_client)
    result = await service.search(
        q,
        sort,
        providers_slug=provider,
        deep=deep,
        scrape_timeout=scrape_timeout,
        process_raw_item_timeout=process_raw_item_timeout,
    )
    collection, query_filter, cursor_sort, transformer = result["apaginate_params"]
    return await apaginate(
        collection,
        query_filter=query_filter,
        sort=cursor_sort,
        transformer=transformer,
    )
