from datetime import datetime
from typing import Dict, List, Optional, Sequence, cast

import motor.motor_asyncio

from betor.entities import CatalogItem, ProviderItem, ProviderItemTorrent
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
        providers = cast(Dict, result.get("providers"))
        return CatalogItem(
            item_type=item_type,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            last_updated=last_updated,
            providers=[
                CatalogItemsRepository.parse_provider_item(data) for data in providers
            ],
        )

    @classmethod
    def parse_provider_item(cls, data: Dict) -> ProviderItem:
        return ProviderItem(
            slug=cast(str, data.get("slug")),
            url=cast(str, data.get("url")),
            languages=cast(List[str], data.get("languages")),
            torrents=[
                CatalogItemsRepository.parse_provider_item_torrent(data)
                for data in cast(List[dict], data.get("torrents"))
            ],
        )

    @classmethod
    def parse_provider_item_torrent(cls, data: Dict) -> ProviderItemTorrent:
        return ProviderItemTorrent(
            magnet_uri=cast(str, data.get("magnet_uri")),
            languages=cast(List[str], data.get("languages")),
            torrent_name=cast(Optional[str], data.get("torrent_name", None)),
            torrent_size=cast(Optional[int], data.get("torrent_size", None)),
            torrent_files=cast(Optional[List[str]], data.get("torrent_files", None)),
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
            {
                "$group": {
                    "_id": {
                        "item_type": "$item_type",
                        "imdb_id": "$imdb_id",
                        "tmdb_id": "$tmdb_id",
                        "provider_slug": "$provider_slug",
                        "provider_url": "$provider_url",
                    },
                    "count": {"$sum": 1},
                    "last_updated": {"$max": "$updated_at"},
                    "torrents": {
                        "$push": {
                            "magnet_uri": "$magnet_uri",
                            "languages": "$languages",
                            "torrent_name": {
                                "$ifNull": ["$torrent_name", "$magnet_dn"]
                            },
                            "torrent_size": "$torrent_size",
                            "torrent_files": "$torrent_files",
                        }
                    },
                }
            },
            {
                "$addFields": {
                    "languages": {
                        "$reduce": {
                            "input": "$torrents.languages",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]},
                        }
                    }
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
                    "providers": {
                        "$push": {
                            "slug": "$_id.provider_slug",
                            "url": "$_id.provider_url",
                            "languages": "$languages",
                            "torrents": "$torrents",
                        }
                    },
                }
            },
        ]
