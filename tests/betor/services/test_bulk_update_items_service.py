from unittest import mock

import motor.motor_asyncio
import pytest

from betor.api.v1.admin.bulk_update_items_schemas import BulkUpdateItemsResponse
from betor.entities import Item
from betor.services.bulk_update_items_service import BulkUpdateItemsService


async def _async_items(items):
    """Helper to create async generator from list."""
    for item in items:
        yield item


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
        return service


class TestBulkUpdateItemsServiceDispatchMaintenanceTasks:
    """Test BulkUpdateItemsService.dispatch_maintenance_tasks.

    Focus: Business logic only (task dispatch count, response structure).
    Trust: Motor library for cursor chaining and async iteration.
    """

    @pytest.mark.asyncio
    async def test_dispatch_one_task_per_item(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        """Verify: For each old item, exactly one Celery task is dispatched."""
        items = [{"_id": f"item-{i}", **item} for i in range(3)]

        # Mock cursor supporting .sort().limit() chaining and async iteration
        mock_cursor = mock.MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__ = lambda self: _async_items(items)

        bulk_update_items_service.items_repository.collection.find.return_value = (
            mock_cursor
        )

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            sig = mock.MagicMock()
            sig.return_value.delay.return_value.id = "task-id"
            celery_mock.signature = sig

            result = await bulk_update_items_service.dispatch_maintenance_tasks()

        # Assert: 3 tasks dispatched
        assert sig.call_count == 3
        assert len(result.task_ids) == 3
        assert result.processed_count == 3
        assert isinstance(result, BulkUpdateItemsResponse)

    @pytest.mark.asyncio
    async def test_response_structure_and_counts(
        self, bulk_update_items_service: BulkUpdateItemsService, item: Item
    ):
        """Verify response has correct structure and counts."""
        items = [{"_id": f"item-{i}", **item} for i in range(5)]

        # Mock cursor with chaining and async iteration
        mock_cursor = mock.MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__ = lambda self: _async_items(items)

        bulk_update_items_service.items_repository.collection.find.return_value = (
            mock_cursor
        )

        with mock.patch(
            "betor.services.bulk_update_items_service.celery_app"
        ) as celery_mock:
            sig = mock.MagicMock()
            sig.return_value.delay.return_value.id = "task-id"
            celery_mock.signature = sig

            result = await bulk_update_items_service.dispatch_maintenance_tasks()

        # Assert: response structure and counts
        assert isinstance(result, BulkUpdateItemsResponse)
        assert result.total_available == 5
        assert result.processed_count == 5
        assert len(result.task_ids) == 5
        assert hasattr(result, "excluded_count")
