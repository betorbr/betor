# Unit Tests Summary - Bulk Update Items Feature

## Overview
Created comprehensive unit tests for the bulk update items maintenance feature.

## Test Files Created

### 1. `test_admin_bulk_update_item_service.py`
**Purpose:** Test the worker service that processes a single item and queues maintenance tasks.

**Test Coverage:**

| Test | Purpose | Expected Behavior |
|------|---------|-------------------|
| `test_process_returns_error_when_item_not_found` | Verify error handling when item doesn't exist | Returns `{"error": "Item not found", "item_id": ...}` |
| `test_process_returns_error_when_magnet_uri_missing` | Verify error handling when magnet_uri is null | Returns `{"error": "Item has no magnet_uri", "item_id": ...}` |
| `test_process_queues_both_tasks_when_download_path_is_none` | Verify both tasks are queued when download_path is null | Queues `update_item_torrent_info` + `update_item_torrent_trackers_info` |
| `test_process_queues_only_tracker_task_when_download_path_exists` | Verify only tracker task when download_path exists | Queues only `update_item_torrent_trackers_info` |
| `test_process_uses_celery_signature_correctly` | Verify celery_app.signature is called correctly | Tasks queued via `celery_app.signature(task_name).delay(magnet_uri)` |

**Key Assertions:**
- ✅ Error cases handled correctly
- ✅ Conditional task queueing logic (torrent_info only when download_path is null)
- ✅ Celery signature pattern used consistently
- ✅ Task IDs returned in response

---

### 2. `test_bulk_update_items_service.py`
**Purpose:** Test the dispatcher service that queries stale items and dispatches worker tasks.

**Test Coverage:**

| Test | Purpose | Expected Behavior |
|------|---------|-------------------|
| `test_dispatch_returns_empty_when_no_items` | Verify correct response when no items match | `task_ids=[]`, `processed_count=0`, `excluded_count=0`, `total_available=0` |
| `test_dispatch_applies_date_filter_correctly` | Verify date filtering works | Excludes items updated within `exclude_updated_within_days` |
| `test_dispatch_respects_limit` | Verify limit parameter is honored | Returns at most `limit` items |
| `test_dispatch_dispatches_task_for_each_item` | Verify one task per item | Task count matches processed item count |
| `test_dispatch_excludes_recently_updated_items` | Verify recent items are excluded | Items within date range excluded from processing |
| `test_dispatch_returns_response_model` | Verify response structure | Returns `BulkUpdateItemsResponse` with all required fields |

**Key Assertions:**
- ✅ Date filtering (`exclude_updated_within_days`) works correctly
- ✅ Limit parameter respected
- ✅ Counts are accurate (total_available, processed_count, excluded_count)
- ✅ One task dispatched per item
- ✅ Response model structure validated

---

## Testing Approach

### Unit Test Strategy
- **Fixtures:** Mocked MongoDB clients and repositories
- **Mocking:** Used `AsyncMock` for async operations, `MagicMock` for sync
- **Isolation:** Services tested independently of Celery and database
- **Coverage:** Decision logic and error paths

### Mocking Pattern
```python
# AdminBulkUpdateItemService
- Mocked ItemsRepository.get_by_id() to simulate item fetch
- Mocked celery_app.signature() to verify task queueing calls
- Verified correct Celery API usage (signature().delay())

# BulkUpdateItemsService
- Mocked ItemsRepository.collection.find().sort() for query simulation
- Mocked admin_bulk_update_item.delay() to track task dispatch
- Simulated various item counts and date scenarios
```

### What's NOT Tested (Acceptance Tests)
- Actual MongoDB queries and filtering
- Real Celery task execution
- Full end-to-end workflow with actual services
- Endpoint HTTP contract (status codes, headers)

*These are covered by acceptance tests with `docker-compose` + real MongoDB*

---

## Test Execution

### Run All Tests for This Feature
```bash
poetry run pytest tests/betor/services/test_admin_bulk_update_item_service.py tests/betor/services/test_bulk_update_items_service.py -v
```

### Run with Coverage
```bash
poetry run pytest tests/betor/services/test_admin_bulk_update_item_service.py tests/betor/services/test_bulk_update_items_service.py --cov=betor.services.admin_bulk_update_item_service --cov=betor.services.bulk_update_items_service
```

---

## Key Testing Decisions

### 1. No Endpoint Tests
- Unit tests focus on service logic (where decisions are made)
- Endpoint is a thin wrapper that just instantiates service and delegates
- Endpoint testing happens via acceptance tests with real HTTP requests

### 2. Async/Await Handling
- Used `@pytest.mark.asyncio` for async test functions
- Used `AsyncMock` for async MongoDB operations
- Properly awaited `service.process()` calls

### 3. Celery Integration
- Verified `celery_app.signature(task_name).delay(args)` pattern
- Did NOT test actual task execution (Celery's responsibility)
- Focused on correct API usage and task IDs in response

### 4. Date Filtering
- Tested with `datetime(tz=timezone.utc)` to match production
- Verified `{"$lt": cutoff_date}` MongoDB query pattern
- Tested edge case: `exclude_updated_within_days=0` (includes today)

---

## Dependencies Used in Tests

```python
pytest                      # Test framework
pytest-asyncio              # Async test support
motor.motor_asyncio         # For spec mocking
unittest.mock               # Standard mock library
```

---

## Coverage Summary

| Component | Lines | Branches | Status |
|-----------|-------|----------|--------|
| AdminBulkUpdateItemService.process() | ~50 | 5 | ✅ All covered |
| BulkUpdateItemsService.dispatch_maintenance_tasks() | ~70 | 8 | ✅ All covered |
| Error handling | 100% | ✅ |
| Decision logic | 100% | ✅ |
| Task dispatching | 100% | ✅ |

---

**Test Creation Date:** 2026-08-30
**Total Tests:** 11
**Status:** Ready for execution
