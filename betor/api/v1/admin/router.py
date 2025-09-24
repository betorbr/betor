from fastapi import APIRouter

from betor.api.fast_api import BetorRequest
from betor.services import (
    AdminNormalizeItemsTMDBIdResult,
    AdminNormalizeItemsTMDBIdService,
)

admin_router = APIRouter()


@admin_router.post("/normalize-items-tmdb-id/")
async def normalize_items_tmdb_id(
    request: BetorRequest,
) -> AdminNormalizeItemsTMDBIdResult:
    service = AdminNormalizeItemsTMDBIdService(request.app.mongodb_client)
    return await service.normalize()
