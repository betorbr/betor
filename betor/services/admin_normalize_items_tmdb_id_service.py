import traceback
from typing import List, Optional, TypedDict

import motor.motor_asyncio

from betor.enums import ItemType
from betor.external_apis import TMDBFindByIdAPI
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
        self.tmdb_find_by_id_api = TMDBFindByIdAPI()

    async def normalize(self) -> AdminNormalizeItemsTMDBIdResult:
        result = AdminNormalizeItemsTMDBIdResult(success=[], failed=[])
        items = await self.items_repository.list_empty_tmdb_id()
        for item in items:
            try:
                assert item["id"] and item["imdb_id"]
                response = await self.tmdb_find_by_id_api.execute(
                    item["imdb_id"], "imdb_id"
                )
                results = response["movie_results"] + response["tv_results"]
                for r in results:
                    if (
                        item["item_type"] == ItemType.movie
                        and r["media_type"] != "movie"
                    ) or (item["item_type"] == ItemType.tv and r["media_type"] != "tv"):
                        continue
                    tmdb_id = str(r["id"])
                    await self.items_repository.update_tmdb_id(item["id"], tmdb_id)
                    result["success"].append(
                        AdminNormalizeItemsTMDBIdResultSucess(
                            item_id=item["id"], imdb_id=item["imdb_id"], tmdb_id=tmdb_id
                        )
                    )
                    break
            except Exception:
                result["failed"].append(
                    AdminNormalizeItemsTMDBIdResultFailed(
                        item_id=item["id"],
                        imdb_id=item["imdb_id"],
                        exception_traceback=traceback.format_exc(),
                    )
                )
        return result
