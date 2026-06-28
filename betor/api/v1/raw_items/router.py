from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.entities import RawItem
from betor.enums import RawItemsSortEnum
from betor.services import GetRawItemService, ListRawItemsService

from .schemas import RawItemSchema

raw_items_router = APIRouter()


@raw_items_router.get("/", response_model=Page[RawItemSchema])
async def list_raw_items(
    request: BetorRequest,
    sort: RawItemsSortEnum = RawItemsSortEnum.inserted_at_desc,
    provider_slug: Optional[str] = None,
    provider_url: Optional[str] = None,
) -> Page[RawItemSchema]:
    service = ListRawItemsService(request.app.mongodb_client)
    collection, query_filter, cursor_sort, transformer = service.apaginate_params(
        sort,
        provider_slug=provider_slug,
        provider_url=provider_url,
    )
    return await apaginate(
        collection,
        query_filter=query_filter,
        sort=cursor_sort,
        transformer=transformer,
    )


@raw_items_router.get("/{raw_item_id}/", response_model=RawItemSchema)
async def get_raw_item(request: BetorRequest, raw_item_id: str) -> RawItem:
    service = GetRawItemService(request.app.mongodb_client)
    raw_item = await service.retrieve(raw_item_id)
    if raw_item is None:
        raise HTTPException(status_code=404, detail="RawItem not found")
    return raw_item
