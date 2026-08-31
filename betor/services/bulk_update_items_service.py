from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import motor.motor_asyncio

from betor.api.v1.admin.bulk_update_items_schemas import BulkUpdateItemsResponse
from betor.celery.app import celery_app
from betor.repositories.items_repository import ItemsRepository


class BulkUpdateItemsService:
    """Service to dispatch maintenance tasks for stale items."""

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)

    async def dispatch_maintenance_tasks(
        self, limit: int = 50, exclude_updated_within_days: int = 30
    ) -> BulkUpdateItemsResponse:
        """
        Query stale items and dispatch Celery maintenance tasks.

        Returns:
            Response with task IDs and counts of processed/excluded items.
        """
        # Build query: items ordered by updated_at DESC, respecting limit
        query_without_date: Dict[str, Any] = {}

        # Execute count before applying date filter (for total_available)
        cursor_total = self.items_repository.collection.find(query_without_date).sort(
            "updated_at", -1
        )

        items_without_filter = []
        async for item in cursor_total.limit(limit):
            items_without_filter.append(item)

        total_available = len(items_without_filter)

        # Build final query with date filter
        query_with_date = dict(query_without_date)
        if exclude_updated_within_days > 0:
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(
                days=exclude_updated_within_days
            )
            query_with_date["updated_at"] = {"$lt": cutoff_date}

        # Fetch stale items
        cursor = self.items_repository.collection.find(query_with_date).sort(
            "updated_at", -1
        )

        items_to_process = []
        async for item in cursor.limit(limit):
            items_to_process.append(item)

        excluded_count = total_available - len(items_to_process)

        # Dispatch Celery task for each item using signature pattern
        task_ids: List[str] = []
        for item in items_to_process:
            item_id = str(item["_id"])
            task = celery_app.signature(
                "admin_bulk_update_item", args=(item_id,)
            ).delay()
            task_ids.append(task.id)

        return BulkUpdateItemsResponse(
            task_ids=task_ids,
            processed_count=len(items_to_process),
            excluded_count=excluded_count,
            total_available=total_available,
        )
