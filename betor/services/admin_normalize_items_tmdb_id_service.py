import traceback
from typing import List, Optional, TypedDict

import motor.motor_asyncio

from betor.enums import ItemType
from betor.external_apis import ITMDBAPI, ITMDBAPIError
from betor.repositories import ItemsRepository


class AdminNormalizeItemsTMDBIdResultSucess(TypedDict):
    item_id: str
    imdb_id: str
    tmdb_id: str


class AdminNormalizeItemsTMDBIdResultFailed(TypedDict):
    item_id: Optional[str]
    imdb_id: Optional[str]
    exception_traceback: str


class AdminNormalizeItemsTMDBIdResult(TypedDict):
    success: List[AdminNormalizeItemsTMDBIdResultSucess]
    failed: List[AdminNormalizeItemsTMDBIdResultFailed]


class AdminNormalizeItemsTMDBIdService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)
        self.itmdb_api = ITMDBAPI()

    async def normalize(self) -> AdminNormalizeItemsTMDBIdResult:
        result = AdminNormalizeItemsTMDBIdResult(success=[], failed=[])
        items = await self.items_repository.list_empty_tmdb_id()
        for item in items:
            try:
                assert item["id"] and item["imdb_id"]
                imdb_id = item["imdb_id"]
                item_type = item["item_type"]

                tmdb_id = None
                if item_type == ItemType.movie:
                    try:
                        resp = await self.itmdb_api.get_movie_by_imdb_id(imdb_id)
                        tmdb_id = str(resp.get("tmdb_id") or resp.get("id"))
                    except ITMDBAPIError:
                        pass
                elif item_type == ItemType.tv:
                    try:
                        resp = await self.itmdb_api.get_tvshow_by_imdb_id(imdb_id)
                        tmdb_id = str(resp.get("tmdb_id") or resp.get("id"))
                    except ITMDBAPIError:
                        pass

                if not tmdb_id:
                    # try both
                    try:
                        resp = await self.itmdb_api.get_movie_by_imdb_id(imdb_id)
                        tmdb_id = str(resp.get("tmdb_id") or resp.get("id"))
                    except ITMDBAPIError:
                        try:
                            resp = await self.itmdb_api.get_tvshow_by_imdb_id(imdb_id)
                            tmdb_id = str(resp.get("tmdb_id") or resp.get("id"))
                        except ITMDBAPIError:
                            pass

                if tmdb_id:
                    await self.items_repository.update_tmdb_id(item["id"], tmdb_id)
                    result["success"].append(
                        AdminNormalizeItemsTMDBIdResultSucess(
                            item_id=item["id"], imdb_id=item["imdb_id"], tmdb_id=tmdb_id
                        )
                    )
                else:
                    raise ValueError(f"Could not find tmdb_id for {imdb_id}")
            except Exception:
                result["failed"].append(
                    AdminNormalizeItemsTMDBIdResultFailed(
                        item_id=item["id"],
                        imdb_id=item["imdb_id"],
                        exception_traceback=traceback.format_exc(),
                    )
                )
        return result
