from typing import Union

from fastapi import APIRouter, HTTPException, Response, status

from betor.api.fast_api import BetorRequest
from betor.exceptions import RawItemNotFound
from betor.services import (
    AdminDeterminesIMDBTMDBIdResult,
    AdminDeterminesIMDBTMDBIdService,
    AdminMapsProviderURLIMDBResult,
    AdminMapsProviderURLIMDBService,
    AdminNormalizeItemsTMDBIdResult,
    AdminNormalizeItemsTMDBIdService,
)
from betor.services.admin_download_items_service import AdminDownloadItemsService

from .schemas import (
    AdminDeterminesIMDBTMDBIdPayload,
    AdminDeterminesIMDBTMDBIdRawItemNotFoundError,
    AdminDeterminesIMDBTMDBIdValueError,
    AdminDownloadItemsResponse,
    AdminMapsProviderURLIMDBPayload,
)

admin_router = APIRouter()


@admin_router.post("/normalize-items-tmdb-id/")
async def normalize_items_tmdb_id(
    request: BetorRequest,
) -> AdminNormalizeItemsTMDBIdResult:
    service = AdminNormalizeItemsTMDBIdService(request.app.mongodb_client)
    return await service.normalize()


@admin_router.post("/determines-imdb-tmdb-id/")
async def determines_imdb_tmdb_id(
    request: BetorRequest, payload: AdminDeterminesIMDBTMDBIdPayload, response: Response
) -> Union[
    AdminDeterminesIMDBTMDBIdResult,
    AdminDeterminesIMDBTMDBIdRawItemNotFoundError,
    AdminDeterminesIMDBTMDBIdValueError,
]:
    service = AdminDeterminesIMDBTMDBIdService(request.app.mongodb_client)
    try:
        return await service.determines(payload.provider_url)
    except RawItemNotFound:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return AdminDeterminesIMDBTMDBIdRawItemNotFoundError()
    except ValueError as e:
        return AdminDeterminesIMDBTMDBIdValueError(message=str(e))


@admin_router.post("/maps-provider-url-imdb")
async def maps_provider_url_imdb(
    request: BetorRequest, payload: AdminMapsProviderURLIMDBPayload
) -> AdminMapsProviderURLIMDBResult:
    service = AdminMapsProviderURLIMDBService(request.app.mongodb_client)
    return await service.maps(payload.provider_url, payload.imdb_id)


@admin_router.get("/download-items/", response_model=AdminDownloadItemsResponse)
async def download_items(request: BetorRequest):
    service = AdminDownloadItemsService(
        request.app.mongodb_client, request.app.redis_client
    )
    try:
        return await service.get_or_create_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
