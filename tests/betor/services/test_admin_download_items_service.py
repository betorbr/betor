import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest import mock

import motor.motor_asyncio
import pytest
import redis

from betor.services.admin_download_items_service import (
    AdminDownloadItemsService,
    DumpCache,
)


@pytest.fixture
def mongodb_client_mock():
    """Mock MongoDB AsyncIO client."""
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.fixture
def redis_client_mock():
    """Mock Redis client."""
    return mock.MagicMock(spec=redis.Redis)


@pytest.fixture
def admin_download_items_service(
    mongodb_client_mock: motor.motor_asyncio.AsyncIOMotorClient,
    redis_client_mock: redis.Redis,
) -> AdminDownloadItemsService:
    """Create an instance of AdminDownloadItemsService with mocked clients."""
    with mock.patch("betor.services.admin_download_items_service.ItemsRepository"):
        service = AdminDownloadItemsService(mongodb_client_mock, redis_client_mock)
        service.items_repository = mock.AsyncMock()
        return service


class TestAdminDownloadItemsServiceInit:
    """Test AdminDownloadItemsService.__init__"""

    def test_init_with_clients(
        self,
        mongodb_client_mock: motor.motor_asyncio.AsyncIOMotorClient,
        redis_client_mock: redis.Redis,
    ):
        """Test that __init__ properly initializes ItemsRepository and redis client."""
        with mock.patch(
            "betor.services.admin_download_items_service.ItemsRepository"
        ) as items_repo_mock:
            service = AdminDownloadItemsService(mongodb_client_mock, redis_client_mock)

            # Verify ItemsRepository was instantiated with mongodb_client
            items_repo_mock.assert_called_once_with(mongodb_client_mock)

            # Verify redis client is stored
            assert service.redis == redis_client_mock


class TestGetCache:
    """Test AdminDownloadItemsService.get_cache"""

    def test_get_cache_returns_none_when_no_cache(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test get_cache returns None when cache key doesn't exist in Redis."""
        admin_download_items_service.redis.get.return_value = None

        result = admin_download_items_service.get_cache()

        assert result is None
        admin_download_items_service.redis.get.assert_called_once()

    def test_get_cache_returns_dump_cache_when_cached(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test get_cache returns DumpCache object when cache exists in Redis."""
        cache_time = datetime(2026, 6, 5, 12, 0, 0)
        cached_data = {
            "it": 100,
            "dts": 5.23,
            "du": "https://example.com/items_dump.json",
            "ga": cache_time.isoformat(),
        }
        admin_download_items_service.redis.get.return_value = json.dumps(
            cached_data
        ).encode()

        result = admin_download_items_service.get_cache()

        assert result is not None
        assert result["items_total"] == 100
        assert result["dump_time_seconds"] == 5.23
        assert result["download_url"] == "https://example.com/items_dump.json"
        assert result["generated_at"] == cache_time

    def test_get_cache_deserializes_datetime(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_cache correctly deserializes datetime from ISO format."""
        iso_datetime = "2026-06-05T14:30:45.123456"
        cached_data = {
            "it": 50,
            "dts": 2.5,
            "du": "https://example.com/dump.json",
            "ga": iso_datetime,
        }
        admin_download_items_service.redis.get.return_value = json.dumps(
            cached_data
        ).encode()

        result = admin_download_items_service.get_cache()

        assert result
        assert result["generated_at"] == datetime.fromisoformat(iso_datetime)


class TestSetCache:
    """Test AdminDownloadItemsService.set_cache"""

    def test_set_cache_serializes_and_stores_data(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that set_cache correctly serializes and stores DumpCache in Redis."""
        cache_time = datetime(2026, 6, 5, 12, 0, 0)
        dump_cache: DumpCache = DumpCache(
            items_total=200,
            dump_time_seconds=8.5,
            download_url="https://example.com/items_dump_20260605.json",
            generated_at=cache_time,
        )

        with mock.patch(
            "betor.services.admin_download_items_service.download_items_cache_settings"
        ) as cache_settings_mock:
            cache_settings_mock.cache_key = "test_cache_key"
            cache_settings_mock.ttl_seconds = 3600

            with mock.patch(
                "betor.services.admin_download_items_service.datetime"
            ) as datetime_mock:
                # Setup datetime mock to return a specific time
                now_time = datetime(2026, 6, 5, 12, 0, 0)
                datetime_mock.now.return_value = now_time
                # Allow datetime constructor to work normally for other calls
                datetime_mock.side_effect = lambda *args, **kw: datetime(*args, **kw)

                admin_download_items_service.set_cache(dump_cache)

                # Verify redis.set was called
                admin_download_items_service.redis.set.assert_called_once()

                # Get the actual call arguments
                call_args = admin_download_items_service.redis.set.call_args
                key = call_args[0][0]
                value = call_args[0][1]
                exat = call_args[1]["exat"]

                # Verify key
                assert key == "test_cache_key"

                # Verify serialized data
                stored_data = json.loads(value)
                assert stored_data["it"] == 200
                assert stored_data["dts"] == 8.5
                assert (
                    stored_data["du"] == "https://example.com/items_dump_20260605.json"
                )
                assert stored_data["ga"] == cache_time.isoformat()

                # Verify TTL is a future timestamp
                expected_expiry = int((now_time + timedelta(seconds=3600)).timestamp())
                assert exat == expected_expiry

    def test_set_cache_uses_correct_settings(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that set_cache uses download_items_cache_settings."""
        dump_cache: DumpCache = DumpCache(
            items_total=10,
            dump_time_seconds=1.0,
            download_url="https://example.com/dump.json",
            generated_at=datetime.now(),
        )

        with mock.patch(
            "betor.services.admin_download_items_service.download_items_cache_settings"
        ) as cache_settings_mock:
            cache_settings_mock.cache_key = "custom_key"
            cache_settings_mock.ttl_seconds = 7200

            with mock.patch(
                "betor.services.admin_download_items_service.datetime"
            ) as datetime_mock:
                now_time = datetime(2026, 6, 5, 12, 0, 0)
                datetime_mock.now.return_value = now_time
                datetime_mock.side_effect = lambda *args, **kw: datetime(*args, **kw)

                admin_download_items_service.set_cache(dump_cache)

                call_args = admin_download_items_service.redis.set.call_args
                assert call_args[0][0] == "custom_key"

                # Verify TTL is a future timestamp
                expected_expiry = int((now_time + timedelta(seconds=7200)).timestamp())
                assert call_args[1]["exat"] == expected_expiry


class TestStoreItems:
    """Test AdminDownloadItemsService.store_items"""

    def test_store_items_creates_file_with_correct_path(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that store_items creates a file with the correct path and filename."""
        items: List[Dict[str, Any]] = [
            {"id": 1, "title": "Item 1"},
            {"id": 2, "title": "Item 2"},
        ]

        with mock.patch(
            "betor.services.admin_download_items_service.fsspec.open"
        ) as fsspec_open_mock:
            mock_file = mock.MagicMock()
            fsspec_open_mock.return_value.__enter__.return_value = mock_file

            with mock.patch(
                "betor.services.admin_download_items_service.download_items_store_settings"
            ) as store_settings_mock:
                store_settings_mock.save_url = "file:///tmp/downloads"
                store_settings_mock.public_download_base_url = None

                with mock.patch(
                    "betor.services.admin_download_items_service.uuid4"
                ) as uuid_mock:
                    test_uuid = "12345678-1234-5678-1234-567812345678"
                    uuid_mock.return_value = test_uuid

                    result = admin_download_items_service.store_items(items)

                    # Verify fsspec.open was called
                    fsspec_open_mock.assert_called_once()
                    call_args = fsspec_open_mock.call_args[0]

                    # Verify path contains save_url and filename with UUID
                    path = call_args[0]
                    assert "file:///tmp/downloads" in path
                    assert path.endswith(f"_{test_uuid}.json")

                    mock_file.write.assert_called()

                    # Result should be just the filename with UUID
                    assert result.endswith(f"_{test_uuid}.json")

    def test_store_items_returns_public_url_when_configured(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that store_items returns public_download_base_url when configured."""
        items: List[Dict[str, Any]] = [{"id": 1, "title": "Item 1"}]

        with mock.patch(
            "betor.services.admin_download_items_service.fsspec.open"
        ) as fsspec_open_mock:
            mock_file = mock.MagicMock()
            fsspec_open_mock.return_value.__enter__.return_value = mock_file

            with mock.patch(
                "betor.services.admin_download_items_service.download_items_store_settings"
            ) as store_settings_mock:
                store_settings_mock.save_url = "file:///tmp/downloads"
                store_settings_mock.public_download_base_url = (
                    "https://example.com/downloads"
                )

                with mock.patch(
                    "betor.services.admin_download_items_service.uuid4"
                ) as uuid_mock:
                    test_uuid = "87654321-4321-8765-4321-876543218765"
                    uuid_mock.return_value = test_uuid

                    result = admin_download_items_service.store_items(items)

                    # Result should use public_download_base_url with UUID in filename
                    assert result.startswith("https://example.com/downloads")
                    assert result.endswith(f"_{test_uuid}.json")

    def test_store_items_serializes_items_to_json(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that store_items correctly serializes items to JSON."""
        items: List[Dict[str, Any]] = [
            {"id": 1, "title": "Item 1", "value": 100},
            {"id": 2, "title": "Item 2", "value": 200},
        ]

        with mock.patch(
            "betor.services.admin_download_items_service.fsspec.open"
        ) as fsspec_open_mock:
            mock_file = mock.MagicMock()
            fsspec_open_mock.return_value.__enter__.return_value = mock_file

            with mock.patch(
                "betor.services.admin_download_items_service.json.dump"
            ) as json_dump_mock:
                with mock.patch(
                    "betor.services.admin_download_items_service.download_items_store_settings"
                ) as store_settings_mock:
                    store_settings_mock.save_url = "file:///tmp"
                    store_settings_mock.public_download_base_url = None

                    with mock.patch(
                        "betor.services.admin_download_items_service.uuid4"
                    ):
                        admin_download_items_service.store_items(items)

                        # Verify json.dump was called with correct data
                        json_dump_mock.assert_called_once()
                        call_args = json_dump_mock.call_args
                        assert call_args[0][0] == items
                        assert call_args[1]["default"] == str

    def test_store_items_strips_trailing_slashes(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that store_items correctly strips trailing slashes from URLs."""
        items: List[Dict[str, Any]] = [{"id": 1}]

        with mock.patch(
            "betor.services.admin_download_items_service.fsspec.open"
        ) as fsspec_open_mock:
            mock_file = mock.MagicMock()
            fsspec_open_mock.return_value.__enter__.return_value = mock_file

            with mock.patch(
                "betor.services.admin_download_items_service.download_items_store_settings"
            ) as store_settings_mock:
                store_settings_mock.save_url = "file:///tmp/downloads/"
                store_settings_mock.public_download_base_url = (
                    "https://example.com/downloads/"
                )

                with mock.patch("betor.services.admin_download_items_service.uuid4"):
                    result = admin_download_items_service.store_items(items)

                    # Path should not have double slashes
                    call_args = fsspec_open_mock.call_args[0]
                    path = call_args[0]
                    assert "downloads//" not in path
                    assert result.count("downloads/") == 1


class TestGetOrCreateDump:
    """Test AdminDownloadItemsService.get_or_create_dump"""

    @pytest.mark.asyncio
    async def test_get_or_create_dump_raises_when_not_enabled(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_or_create_dump raises RuntimeError when store is not enabled."""
        with mock.patch(
            "betor.services.admin_download_items_service.download_items_store_settings"
        ) as store_settings_mock:
            store_settings_mock.enabled = False

            with pytest.raises(RuntimeError) as exc_info:
                await admin_download_items_service.get_or_create_dump()

            assert "Download items store not enabled" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_or_create_dump_returns_cached_when_available(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_or_create_dump returns cached dump when available."""
        cache_time = datetime(2026, 6, 5, 12, 0, 0)
        cached_dump: DumpCache = DumpCache(
            items_total=100,
            dump_time_seconds=5.0,
            download_url="https://example.com/dump.json",
            generated_at=cache_time,
        )

        with mock.patch.object(
            admin_download_items_service,
            "get_cache",
            return_value=cached_dump,
        ):
            with mock.patch(
                "betor.services.admin_download_items_service.download_items_store_settings"
            ) as store_settings_mock:
                store_settings_mock.enabled = True

                result = await admin_download_items_service.get_or_create_dump()

                assert result == cached_dump
                admin_download_items_service.get_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_dump_creates_dump_when_no_cache(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_or_create_dump creates new dump when no cache exists."""
        # Setup
        items = [
            {"id": 1, "title": "Item 1"},
            {"id": 2, "title": "Item 2"},
        ]
        duration = 2.5

        admin_download_items_service.items_repository.dump_all_items.return_value = (
            duration,
            items,
        )

        with (
            mock.patch.object(
                admin_download_items_service,
                "get_cache",
                return_value=None,
            ),
            mock.patch.object(
                admin_download_items_service,
                "set_cache",
            ),
        ):
            with mock.patch(
                "betor.services.admin_download_items_service.ItemSchema"
            ) as item_schema_mock:
                schema_instance = mock.MagicMock()
                schema_instance.model_dump.return_value = items[0]
                item_schema_mock.return_value = schema_instance

                with mock.patch.object(
                    admin_download_items_service,
                    "store_items",
                    return_value="https://example.com/dump.json",
                ):
                    with mock.patch(
                        "betor.services.admin_download_items_service.download_items_store_settings"
                    ) as store_settings_mock:
                        store_settings_mock.enabled = True

                        result = await admin_download_items_service.get_or_create_dump()

                        # Verify the dump was created and cached
                        assert result["items_total"] == 2
                        assert result["dump_time_seconds"] == 2.5
                        assert result["download_url"] == "https://example.com/dump.json"
                        admin_download_items_service.set_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_dump_formats_items_with_schema(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_or_create_dump formats items using ItemSchema.model_dump()."""
        items = [{"id": 1, "raw": "data"}]
        admin_download_items_service.items_repository.dump_all_items.return_value = (
            1.0,
            items,
        )

        with (
            mock.patch.object(
                admin_download_items_service,
                "get_cache",
                return_value=None,
            ),
            mock.patch.object(
                admin_download_items_service,
                "set_cache",
            ),
        ):
            with mock.patch(
                "betor.services.admin_download_items_service.ItemSchema"
            ) as item_schema_mock:
                formatted_item = {"id": 1, "formatted": "data"}
                schema_instance = mock.MagicMock()
                schema_instance.model_dump.return_value = formatted_item
                item_schema_mock.return_value = schema_instance

                with mock.patch.object(
                    admin_download_items_service,
                    "store_items",
                    return_value="https://example.com/dump.json",
                ):
                    with mock.patch(
                        "betor.services.admin_download_items_service.download_items_store_settings"
                    ) as store_settings_mock:
                        store_settings_mock.enabled = True

                        await admin_download_items_service.get_or_create_dump()

                        # Verify ItemSchema was called
                        item_schema_mock.assert_called_with(**items[0])
                        schema_instance.model_dump.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_dump_calls_store_items(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_or_create_dump calls store_items with formatted items."""
        items = [{"id": 1}]
        admin_download_items_service.items_repository.dump_all_items.return_value = (
            1.0,
            items,
        )

        with (
            mock.patch.object(
                admin_download_items_service,
                "get_cache",
                return_value=None,
            ),
            mock.patch.object(
                admin_download_items_service,
                "set_cache",
            ),
        ):
            with mock.patch(
                "betor.services.admin_download_items_service.ItemSchema"
            ) as item_schema_mock:
                formatted_item = {"id": 1, "formatted": True}
                schema_instance = mock.MagicMock()
                schema_instance.model_dump.return_value = formatted_item
                item_schema_mock.return_value = schema_instance

                with mock.patch.object(
                    admin_download_items_service,
                    "store_items",
                    return_value="https://example.com/dump.json",
                ) as store_items_mock:
                    with mock.patch(
                        "betor.services.admin_download_items_service.download_items_store_settings"
                    ) as store_settings_mock:
                        store_settings_mock.enabled = True

                        await admin_download_items_service.get_or_create_dump()

                        # Verify store_items was called with formatted items
                        store_items_mock.assert_called_once()
                        call_args = store_items_mock.call_args[0][0]
                        assert call_args == [formatted_item]

    @pytest.mark.asyncio
    async def test_get_or_create_dump_caches_result(
        self, admin_download_items_service: AdminDownloadItemsService
    ):
        """Test that get_or_create_dump caches the created dump."""
        items = [{"id": 1}]
        admin_download_items_service.items_repository.dump_all_items.return_value = (
            1.5,
            items,
        )

        with (
            mock.patch.object(
                admin_download_items_service,
                "get_cache",
                return_value=None,
            ),
            mock.patch.object(
                admin_download_items_service,
                "set_cache",
            ),
        ):
            with mock.patch(
                "betor.services.admin_download_items_service.ItemSchema"
            ) as item_schema_mock:
                schema_instance = mock.MagicMock()
                schema_instance.model_dump.return_value = {"id": 1}
                item_schema_mock.return_value = schema_instance

                with mock.patch.object(
                    admin_download_items_service,
                    "store_items",
                    return_value="https://example.com/dump.json",
                ):
                    with mock.patch(
                        "betor.services.admin_download_items_service.download_items_store_settings"
                    ) as store_settings_mock:
                        store_settings_mock.enabled = True

                        with mock.patch(
                            "betor.services.admin_download_items_service.datetime"
                        ) as datetime_mock:
                            now_time = datetime(2026, 6, 5, 12, 0, 0)
                            datetime_mock.now.return_value = now_time
                            datetime_mock.side_effect = lambda *args, **kw: datetime(
                                *args, **kw
                            )

                            await admin_download_items_service.get_or_create_dump()

                            # Verify set_cache was called
                            admin_download_items_service.set_cache.assert_called_once()
                            cached_obj = (
                                admin_download_items_service.set_cache.call_args[0][0]
                            )
                            assert cached_obj["items_total"] == 1
                            assert cached_obj["dump_time_seconds"] == 1.5
                            assert (
                                cached_obj["download_url"]
                                == "https://example.com/dump.json"
                            )
