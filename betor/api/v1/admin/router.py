from typing import Union

from fastapi import APIRouter, Response, status

from betor.api.fast_api import BetorRequest
from betor.exceptions import RawItemNotFound
from betor.services import (
    AdminDeterminesIMDBTMDBIdResult,
    AdminDeterminesIMDBTMDBIdService,
    AdminNormalizeItemsTMDBIdResult,
    AdminNormalizeItemsTMDBIdService,
)

from .schemas import (
    AdminDeterminesIMDBTMDBIdPayload,
    AdminDeterminesIMDBTMDBIdRawItemNotFoundError,
    AdminDeterminesIMDBTMDBIdValueError,
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
