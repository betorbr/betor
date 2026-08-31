from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import motor.motor_asyncio

from betor.api.v1.admin.bulk_update_items_schemas import (
    BulkUpdateItemsResponse,
    UpdatedItem,
)
from betor.celery.app import celery_app
from betor.repositories.items_repository import ItemsRepository


class BulkUpdateItemsService:
    """Service to dispatch maintenance tasks for stale items."""

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def dispatch_maintenance_tasks(
        self,
        limit: int = 50,
        exclude_updated_within_days: int = 30,
        torrent_is_dying: Optional[bool] = None,
    ) -> BulkUpdateItemsResponse:
        """
        Query stale items and dispatch Celery maintenance tasks.

        Returns:
            Response with dispatched item/task pairs and complete-set counts.
        """
        item_filter: Dict[str, Any] = (
            {"torrent_is_dying": torrent_is_dying}
            if torrent_is_dying is not None
            else {}
        )
        query_with_date = item_filter.copy()
        recent_query = item_filter.copy()
        if exclude_updated_within_days > 0:
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(
                days=exclude_updated_within_days
            )
            query_with_date["updated_at"] = {"$lt": cutoff_date}
            recent_query["updated_at"] = {"$gte": cutoff_date}

        filtered_count = 0
        if recent_query:
            filtered_count = await self.items_repository.collection.count_documents(
                recent_query
            )
        remaining_count = await self.items_repository.collection.count_documents(
            query_with_date
        )

        cursor = (
            self.items_repository.collection.find(query_with_date)
            .sort("updated_at", -1)
            .limit(limit)
        )

        updated_items: List[UpdatedItem] = []
        async for item in cursor:
            item_id = str(item["_id"])
            task = celery_app.signature(
                "admin_bulk_update_item", args=(item_id,)
            ).delay()
            updated_items.append(UpdatedItem(task_id=task.id, item_id=item_id))

        return BulkUpdateItemsResponse(
            updated_items=updated_items,
            processed_count=len(updated_items),
            filtered_count=filtered_count,
            remaining_count=remaining_count,
        )
