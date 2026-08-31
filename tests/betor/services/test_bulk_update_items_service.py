from unittest import mock

import motor.motor_asyncio
import pytest

from betor.api.v1.admin.bulk_update_items_schemas import BulkUpdateItemsResponse
from betor.entities import Item
from betor.services.bulk_update_items_service import BulkUpdateItemsService


@pytest.fixture
def mongodb_client_mock():
    """Mock MongoDB AsyncIO client."""
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def bulk_update_items_service(
    mongodb_client_mock: motor.motor_asyncio.AsyncIOMotorClient,
) -> BulkUpdateItemsService:
    """Create service with mocked repository."""
    with mock.patch("betor.services.bulk_update_items_service.ItemsRepository"):
        service = BulkUpdateItemsService(mongodb_client_mock)
        service.items_repository = mock.MagicMock()
        service.items_repository.collection = mock.MagicMock()
        service.items_repository.collection.count_documents = mock.AsyncMock()
        return service


class TestBulkUpdateItemsServiceDispatchMaintenanceTasks:
    """Test BulkUpdateItemsService.dispatch_maintenance_tasks.

    Focus: Business logic only (count queries, task dispatch, response structure).
    """

    @pytest.mark.asyncio
    async def test_dispatch_one_task_per_item(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        """Verify: For each old item, exactly one Celery task is dispatched."""
        items = [{"_id": f"item-{i}", **item} for i in range(3)]

        cursor = mock.MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.__aiter__.return_value = items
        bulk_update_items_service.items_repository.collection.find.return_value = cursor
        bulk_update_items_service.items_repository.collection.count_documents.side_effect = [
            3,
            3,
        ]

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            sig = mock.MagicMock()
            task_signatures = [mock.MagicMock() for _ in range(3)]
            sig.side_effect = task_signatures
            for index, task_signature in enumerate(task_signatures):
                task_signature.delay.return_value.id = f"task-{index}"
            celery_mock.signature = sig

            result = await bulk_update_items_service.dispatch_maintenance_tasks()

        assert sig.call_count == 3
        assert [updated_item.model_dump() for updated_item in result.updated_items] == [
            {"task_id": "task-0", "item_id": "item-0"},
            {"task_id": "task-1", "item_id": "item-1"},
            {"task_id": "task-2", "item_id": "item-2"},
        ]
        assert result.processed_count == 3
        assert isinstance(result, BulkUpdateItemsResponse)
        cursor.limit.assert_called_once_with(50)

    @pytest.mark.asyncio
    async def test_counts_include_all_items_when_limit_is_smaller(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        """Verify counts are not limited to the dispatched items."""
        all_items = [{"_id": f"item-{i}", **item} for i in range(14)]
        eligible_items = all_items[:10]

        cursor = mock.MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.__aiter__.return_value = eligible_items[:1]
        bulk_update_items_service.items_repository.collection.find.return_value = cursor
        bulk_update_items_service.items_repository.collection.count_documents.side_effect = [
            4,
            10,
        ]

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            sig = mock.MagicMock()
            sig.return_value.delay.return_value.id = "task-id"
            celery_mock.signature = sig

            result = await bulk_update_items_service.dispatch_maintenance_tasks(limit=1)

        assert result.filtered_count == 4
        assert result.remaining_count == 10
        assert result.processed_count == 1
        assert len(result.updated_items) == 1
        assert (
            bulk_update_items_service.items_repository.collection.count_documents.call_count
            == 2
        )
        count_queries = [
            call.args[0]
            for call in bulk_update_items_service.items_repository.collection.count_documents.await_args_list
        ]
        assert count_queries[0]["updated_at"].keys() == {"$gte"}
        assert count_queries[1]["updated_at"].keys() == {"$lt"}
        cursor.limit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_no_eligible_items_returns_empty_dispatch(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        """Verify recent items are counted and no task is dispatched."""
        cursor = mock.MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.__aiter__.return_value = []
        bulk_update_items_service.items_repository.collection.find.return_value = cursor
        bulk_update_items_service.items_repository.collection.count_documents.side_effect = [
            2,
            0,
        ]

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            result = await bulk_update_items_service.dispatch_maintenance_tasks()

        assert result.filtered_count == 2
        assert result.remaining_count == 0
        assert result.processed_count == 0
        assert result.updated_items == []
        celery_mock.signature.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_recent_items_counts_all_eligible_items(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        """Verify no items are filtered when every item is eligible."""
        items = [{"_id": f"item-{i}", **item} for i in range(3)]

        cursor = mock.MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.__aiter__.return_value = items[:2]
        bulk_update_items_service.items_repository.collection.find.return_value = cursor
        bulk_update_items_service.items_repository.collection.count_documents.side_effect = [
            0,
            3,
        ]

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            celery_mock.signature.return_value.delay.return_value.id = "task-id"
            result = await bulk_update_items_service.dispatch_maintenance_tasks(limit=2)

        assert result.filtered_count == 0
        assert result.remaining_count == 3
        assert result.processed_count == 2
        assert len(result.updated_items) == 2

    @pytest.mark.asyncio
    async def test_zero_exclusion_days_counts_all_items_as_eligible(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        items = [{"_id": f"item-{i}", **item} for i in range(2)]
        cursor = mock.MagicMock()
        cursor.sort.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.__aiter__.return_value = items
        bulk_update_items_service.items_repository.collection.find.return_value = cursor
        bulk_update_items_service.items_repository.collection.count_documents.return_value = (
            2
        )

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            celery_mock.signature.return_value.delay.return_value.id = "task-id"
            result = await bulk_update_items_service.dispatch_maintenance_tasks(
                exclude_updated_within_days=0
            )

        assert result.filtered_count == 0
        assert result.remaining_count == 2
        bulk_update_items_service.items_repository.collection.count_documents.assert_awaited_once_with(
            {}
        )
