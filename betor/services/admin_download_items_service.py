import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypedDict
from uuid import uuid4

import fsspec
import motor.motor_asyncio
import redis

from betor.api.v1.items.schemas import ItemSchema
from betor.repositories.items_repository import ItemsRepository
from betor.settings import (
    download_items_cache_settings,
    download_items_store_settings,
)


class DumpCache(TypedDict):
    items_total: int
    dump_time_seconds: float
    download_url: str
    generated_at: datetime


class AdminDownloadItemsService:
    def __init__(
        self,
        mongodb_client: motor.motor_asyncio.AsyncIOMotorClient,
        redis_client: redis.Redis,
    ):
        self.items_repository = ItemsRepository(mongodb_client)
        self.redis = redis_client

    def get_cache(self) -> Optional[DumpCache]:
        if cached := self.redis.get(download_items_cache_settings.cache_key):
            cache_data = json.loads(cached)
            return DumpCache(
                items_total=cache_data["it"],
                dump_time_seconds=cache_data["dts"],
                download_url=cache_data["du"],
                generated_at=datetime.fromisoformat(cache_data["ga"]),
            )
        return None

    def set_cache(self, cache_obj: DumpCache) -> None:
        expired_at = datetime.now() + timedelta(
            seconds=download_items_cache_settings.ttl_seconds
        )
        self.redis.set(
            download_items_cache_settings.cache_key,
            json.dumps(
                {
                    "it": cache_obj["items_total"],
                    "dts": cache_obj["dump_time_seconds"],
                    "du": cache_obj["download_url"],
                    "ga": cache_obj["generated_at"].isoformat(),
                }
            ),
            exat=int(expired_at.timestamp()),
        )

    def store_items(self, formatted_items: List[Dict[str, Any]]) -> str:
        assert download_items_store_settings.save_url
        filename = f"items_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4()}.json"
        path = f"{download_items_store_settings.save_url.rstrip('/')}/{filename}"
        with fsspec.open(path, "w") as f:
            json.dump(formatted_items, f, default=str)

        if download_items_store_settings.public_download_base_url:
            return f"{download_items_store_settings.public_download_base_url.rstrip('/')}/{filename}"
        return filename

    async def get_or_create_dump(self) -> DumpCache:
        if not download_items_store_settings.enabled:
            raise RuntimeError(
                "Download items store not enabled. Please configure the save_url in the settings download_items_store_settings."
            )
        cached = self.get_cache()
        if cached:
            return cached
        duration, items = await self.items_repository.dump_all_items()
        formatted_items = [ItemSchema(**item).model_dump() for item in items]
        download_url = self.store_items(formatted_items)
        cache_obj = DumpCache(
            items_total=len(formatted_items),
            dump_time_seconds=duration,
            download_url=download_url,
            generated_at=datetime.now(),
        )
        self.set_cache(cache_obj)
        return cache_obj
