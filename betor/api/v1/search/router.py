from typing import Annotated, List, Optional

from fastapi import APIRouter, Query
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.api.v1.items.schemas import ItemSchema
from betor.enums import ItemsSortEnum, ItemType
from betor.providers import ProviderSlug
from betor.services import SearchService

from .schemas import SearchPage

search_router = APIRouter()


@search_router.get("/")
async def search(
    request: BetorRequest,
    q: str,
    sort: ItemsSortEnum = ItemsSortEnum.inserted_at_desc,
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    item_type: Annotated[Optional[List[ItemType]], Query()] = None,
    deep: int = 3,
    scrape_timeout: int = 30,
    process_raw_item_timeout: int = 30,
    provider: Annotated[Optional[List[ProviderSlug]], Query()] = None,
) -> SearchPage[ItemSchema]:
    service = SearchService(request.app.mongodb_client, request.app.redis_client)
    result = await service.search(
        q,
        sort,
        imdb_id=imdb_id,
        tmdb_id=tmdb_id,
        providers_slug=provider,
        item_types=item_type,
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
        additional_data={
            "q": result["q"],
            "job_monitor": result["job_monitor"],
        },
    )
