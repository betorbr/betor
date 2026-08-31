from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import Item
from betor.services.admin_bulk_update_item_service import AdminBulkUpdateItemService


@pytest.fixture
def mongodb_client_mock():
    """Mock MongoDB AsyncIO client."""
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def admin_bulk_update_item_service(
    mongodb_client_mock: motor.motor_asyncio.AsyncIOMotorClient,
) -> AdminBulkUpdateItemService:
    """Create an instance with mocked repositories."""
    service = AdminBulkUpdateItemService(mongodb_client_mock)
    service.items_repository = mock.AsyncMock()
    return service


class TestAdminBulkUpdateItemServiceProcess:
    """Test AdminBulkUpdateItemService.process"""

    @pytest.mark.asyncio
    async def test_process_raises_error_when_item_not_found(
        self, admin_bulk_update_item_service: AdminBulkUpdateItemService
    ):
        """Test process raises ValueError when item doesn't exist."""
        admin_bulk_update_item_service.items_repository.get_by_id.return_value = None
        item_id = "507f1f77bcf86cd799439011"

        with pytest.raises(ValueError, match="Item not found"):
            await admin_bulk_update_item_service.process(item_id)

        admin_bulk_update_item_service.items_repository.get_by_id.assert_called_once_with(
            item_id
        )

    @pytest.mark.asyncio
    async def test_process_raises_error_when_magnet_uri_missing(
        self, admin_bulk_update_item_service: AdminBulkUpdateItemService, item: Item
    ):
        """Test process raises ValueError when item has no magnet_uri."""
        item_without_magnet = {**item, "magnet_uri": None}
        admin_bulk_update_item_service.items_repository.get_by_id.return_value = (
            item_without_magnet
        )
        item_id = "507f1f77bcf86cd799439011"

        with pytest.raises(ValueError, match="Item has no magnet_uri"):
            await admin_bulk_update_item_service.process(item_id)

    @pytest.mark.asyncio
    async def test_process_queues_both_tasks_when_download_path_is_none(
        self, admin_bulk_update_item_service: AdminBulkUpdateItemService, item: Item
    ):
        """Test process queues both torrent and tracker tasks when download_path is None."""
        magnet_uri = item["magnet_uri"]
        item_with_no_download_path = {**item, "download_path": None}
        admin_bulk_update_item_service.items_repository.get_by_id.return_value = (
            item_with_no_download_path
        )
        item_id = str(item["id"])

        with mock.patch(
            "betor.services.admin_bulk_update_item_service.celery_app"
        ) as celery_mock:
            celery_mock.signature.return_value.delay.return_value.id = "task-uuid-1"

            result = await admin_bulk_update_item_service.process(item_id)

        assert result["item_id"] == item_id
        assert result["magnet_uri"] == magnet_uri
        assert len(result["queued_tasks"]) == 2
        assert result["queued_tasks"][0]["task"] == "update_item_torrent_info"
        assert result["queued_tasks"][1]["task"] == "update_item_torrent_trackers_info"
        assert all("task_id" in task for task in result["queued_tasks"])

    @pytest.mark.asyncio
    async def test_process_queues_only_tracker_task_when_download_path_exists(
        self, admin_bulk_update_item_service: AdminBulkUpdateItemService, item: Item
    ):
        """Test process queues only tracker task when download_path exists."""
        magnet_uri = item["magnet_uri"]
        item_with_download_path = {**item, "download_path": "/some/path"}
        admin_bulk_update_item_service.items_repository.get_by_id.return_value = (
            item_with_download_path
        )
        item_id = str(item["id"])

        with mock.patch(
            "betor.services.admin_bulk_update_item_service.celery_app"
        ) as celery_mock:
            celery_mock.signature.return_value.delay.return_value.id = "task-uuid-2"

            result = await admin_bulk_update_item_service.process(item_id)

        assert result["item_id"] == item_id
        assert result["magnet_uri"] == magnet_uri
        assert len(result["queued_tasks"]) == 1
        assert result["queued_tasks"][0]["task"] == "update_item_torrent_trackers_info"

    @pytest.mark.asyncio
    async def test_process_uses_celery_signature_correctly(
        self, admin_bulk_update_item_service: AdminBulkUpdateItemService, item: Item
    ):
        """Test process calls celery_app.signature with correct task names."""
        item_with_no_download = {**item, "download_path": None}
        admin_bulk_update_item_service.items_repository.get_by_id.return_value = (
            item_with_no_download
        )
        item_id = str(item["id"])
        magnet_uri = item["magnet_uri"]

        with mock.patch(
            "betor.services.admin_bulk_update_item_service.celery_app"
        ) as celery_mock:
            mock_signature = mock.MagicMock()
            celery_mock.signature.return_value = mock_signature
            mock_signature.delay.return_value.id = "task-id"

            await admin_bulk_update_item_service.process(item_id)

            # Verify signature was called with correct task names
            calls = celery_mock.signature.call_args_list
            assert len(calls) == 2
            assert calls[0][0][0] == "update_item_torrent_info"
            assert calls[1][0][0] == "update_item_torrent_trackers_info"

            # Verify delay was called with magnet_uri
            assert mock_signature.delay.call_count == 2
            mock_signature.delay.assert_any_call(magnet_uri)
