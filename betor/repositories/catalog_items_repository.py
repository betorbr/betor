from datetime import datetime
from typing import Dict, List, Sequence, cast

import motor.motor_asyncio

from betor.entities import CatalogItem, ProviderPage
from betor.enums import ItemType
from betor.settings import database_mongodb_settings


class CatalogItemsRepository:
    @classmethod
    def parse_result(cls, result: Dict) -> CatalogItem:
        id_value = cast(Dict, result.get("_id"))
        item_type = cast(ItemType, id_value.get("item_type"))
        imdb_id = id_value.get("imdb_id")
        tmdb_id = id_value.get("tmdb_id")
        last_updated = cast(datetime, result.get("last_updated"))
        provider_pages = cast(Dict, result.get("provider_pages"))
        return CatalogItem(
            item_type=item_type,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            last_updated=last_updated,
            provider_pages=[
                CatalogItemsRepository.parse_provider_page(data)
                for data in provider_pages
            ],
        )

    @classmethod
    def parse_provider_page(cls, data: Dict) -> ProviderPage:
        return ProviderPage(
            slug=cast(str, data.get("slug")),
            url=cast(str, data.get("url")),
            languages=data.get("languages", []),
            torrent_names=data.get("torrent_names", []),
        )

    @classmethod
    def parse_results(cls, results: Sequence[Dict]) -> Sequence[CatalogItem]:
        return [CatalogItemsRepository.parse_result(r) for r in results]

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.mongodb_client = mongodb_client

    @property
    def database(self) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        return self.mongodb_client.get_database(
            database_mongodb_settings.betor_database
        )

    @property
    def collection(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.database["items"]

    @property
    def aggr_pipeline(self) -> List[Dict]:
        return [
            {
                "$match": {
                    "item_type": {"$ne": None},
                    "updated_at": {"$ne": None},
                    "$or": [
                        {"imdb_id": {"$ne": None}},
                        {"tmdb_id": {"$ne": None}},
                    ],
                }
            },
            {"$unwind": {"path": "$languages", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": {
                        "item_type": "$item_type",
                        "imdb_id": "$imdb_id",
                        "tmdb_id": "$tmdb_id",
                        "provider_slug": "$provider_slug",
                        "provider_url": "$provider_url",
                    },
                    "languages": {"$addToSet": "$languages"},
                    "torrent_names": {"$addToSet": "$torrent_name"},
                    "count": {"$sum": 1},
                    "last_updated": {"$max": "$updated_at"},
                }
            },
            {
                "$group": {
                    "_id": {
                        "item_type": "$_id.item_type",
                        "imdb_id": "$_id.imdb_id",
                        "tmdb_id": "$_id.tmdb_id",
                    },
                    "count": {"$sum": "$count"},
                    "last_updated": {"$max": "$last_updated"},
                    "provider_pages": {
                        "$push": {
                            "slug": "$_id.provider_slug",
                            "url": "$_id.provider_url",
                            "languages": "$languages",
                            "torrent_names": "$torrent_names",
                        }
                    },
                }
            },
        ]
