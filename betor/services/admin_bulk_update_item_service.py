from typing import Any, Dict, List

import motor.motor_asyncio

from betor.celery.app import celery_app
from betor.repositories.items_repository import ItemsRepository


class AdminBulkUpdateItemService:
    """
    Admin service to queue maintenance tasks for a single item during bulk updates.

    Decides which update tasks to run based on item's missing fields:
    - Queues update_item_torrent_info only if download_path is NULL
    - Always queues update_item_torrent_trackers_info
    """

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)
        self.mongodb_client = mongodb_client

    async def process(self, item_id: str) -> Dict[str, Any]:
        """
        Queue maintenance tasks for a single item.

        Args:
            item_id: ObjectId of the item as string

        Returns:
            Dict with item_id, magnet_uri, and list of queued task IDs

        Raises:
            ValueError: If item not found or magnet_uri is missing
        """
        # Fetch item to check which updates are needed
        item = await self.items_repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        magnet_uri = item.get("magnet_uri")
        if not magnet_uri:
            raise ValueError(f"Item has no magnet_uri: {item_id}")

        # Decide which tasks to run based on item state
        tasks_to_queue: List[tuple] = []

        # Decision 1: Queue torrent info only if download_path is missing
        if item.get("download_path") is None:
            tasks_to_queue.append(("update_item_torrent_info", (magnet_uri,)))

        # Decision 2: Always queue tracker info (peers/seeds counts)
        tasks_to_queue.append(("update_item_torrent_trackers_info", (magnet_uri,)))

        # Queue tasks and collect task IDs
        queued_tasks = []
        for task_name, task_args in tasks_to_queue:
            result = celery_app.signature(task_name).delay(*task_args)
            queued_tasks.append({"task": task_name, "task_id": result.id})

        return {
            "item_id": item_id,
            "magnet_uri": magnet_uri,
            "queued_tasks": queued_tasks,
        }
