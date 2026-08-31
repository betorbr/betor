# BulkUpdateItemsService - Test Implementation Guide

**Service**: `betor/services/bulk_update_items_service.py`
**Test File**: `tests/betor/services/test_bulk_update_items_service.py`
**Status**: Awaiting Implementation (See Recommendations)
**Date**: 2026-08-30

---

## Service Overview

`BulkUpdateItemsService.dispatch_maintenance_tasks()` performs:

1. Query repository for **all items** → count as `total_available`
2. Query repository for **old items** (apply date filter) → to process
3. For each old item → dispatch Celery task via `celery_app.signature()`
4. Return: `BulkUpdateItemsResponse(task_ids, processed_count, excluded_count, total_available)`

---

## Test Scope: What Should Be Tested

### ✅ Test 1: Task Dispatch Count (Core Logic)

**Business Question**: "Do we dispatch exactly one task per item?"

```python
@pytest.mark.asyncio
async def test_dispatch_one_task_per_item(service, item):
    """Verify: for each item, one Celery task is dispatched."""
    items = [{"_id": f"item-{i}", **item} for i in range(5)]

    # Mock repository to return 5 items
    service.items_repository.collection.find.return_value = items

    # Mock Celery signature
    with mock.patch("betor.celery.app.celery_app") as celery_mock:
        sig_mock = mock.MagicMock()
        sig_mock.return_value.delay.return_value.id = "task-uuid"
        celery_mock.signature = sig_mock

        result = await service.dispatch_maintenance_tasks(limit=50)

    # Assert: 5 tasks dispatched
    assert sig_mock.call_count == 5
    assert len(result.task_ids) == 5
    assert result.processed_count == 5
```

**Why**: Tests OUR logic (loop through items, dispatch once per item). Does NOT test Motor or Celery internals.

---

### ✅ Test 2: Response Structure (Contract)

**Business Question**: "Does the response have the right shape and initial values?"

```python
@pytest.mark.asyncio
async def test_response_structure(service, item):
    """Verify response is BulkUpdateItemsResponse with correct fields."""
    items = [{"_id": "test", **item}]
    service.items_repository.collection.find.return_value = items

    with mock.patch("betor.celery.app.celery_app"):
        result = await service.dispatch_maintenance_tasks()

    # Assert: correct type and structure
    assert isinstance(result, BulkUpdateItemsResponse)
    assert len(result.task_ids) == 1
    assert result.processed_count == 1
    assert result.total_available == 1
    assert result.excluded_count == 0
```

**Why**: Tests the service contract. Does NOT test library response serialization.

---

## Test Scope: What Should NOT Be Tested

### ❌ Do NOT Test: Date Filtering Logic

**Why**: Repository's responsibility. Test in `test_items_repository.py`.

**Example of WRONG test**:
```python
# WRONG: This belongs in repository tests
def test_date_filtering_correctly():
    now = datetime.now(tz=timezone.utc)
    old_item = {**item, "updated_at": now - timedelta(days=35)}
    recent_item = {**item, "updated_at": now - timedelta(days=5)}

    # Complex mocking to test date logic...
    # NO! This is repository logic!
```

**Correct approach**:
- Repository test: "Does find_old_items() return items > 30 days old?"
- Service test: "Does repository method get called?"

---

### ❌ Do NOT Test: Motor Cursor Chaining

**Why**: Motor's responsibility. We trust the library.

**Example of WRONG test**:
```python
# WRONG: Testing Motor, not our code
def test_cursor_sort_and_limit():
    cursor = create_motor_cursor()
    sorted_cursor = cursor.sort("_id", -1)
    limited = sorted_cursor.limit(50)
    items = [item async for item in limited]
    # NO! This tests Motor!
```

**Correct approach**: Mock repository. Don't mock Motor cursor.

---

### ❌ Do NOT Test: Motor Async Iteration

**Why**: Motor handles `async for` protocol. We just use it.

**Example of WRONG test**:
```python
# WRONG: Testing Motor's async iteration
def test_async_iteration_over_cursor():
    cursor = motor_cursor()
    count = 0
    async for item in cursor:
        count += 1
    # NO! This tests Motor's __aiter__ and __anext__!
```

**Correct approach**: Mock repository returns list. Motor iteration is transparent.

---

### ❌ Do NOT Test: Limit Parameter Behavior

**Why**: Motor's API. We call it; Motor implements it.

**Example of WRONG test**:
```python
# WRONG: Testing Motor's limit()
def test_limit_parameter_reduces_results():
    items_100 = [{"_id": i} for i in range(100)]
    cursor = create_motor_cursor(items_100)
    limited = cursor.limit(50)
    results = [item async for item in limited]
    assert len(results) == 50
    # NO! This tests Motor's limit()!
```

**Correct approach**: Service calls `cursor.limit(50)`. Motor ensures 50 results. We don't verify Motor.

---

### ❌ Do NOT Test: Celery Task Registration

**Why**: Celery's responsibility. We mock and assert call.

**Example of WRONG test**:
```python
# WRONG: Testing Celery internals
def test_celery_task_gets_registered():
    # Mocking Celery's task registry...
    # Testing task.apply_async() internals...
    # NO! This is Celery's job!
```

**Correct approach**: Mock `celery_app.signature()`. Assert it was called with correct args.

---

## Recommended Mock Setup

### Fixture Pattern (Copy from `test_admin_download_items_service.py`)

```python
@pytest.fixture
def mongodb_client_mock():
    """Mock MongoDB AsyncIO client."""
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)

@pytest.fixture
def bulk_update_items_service(mongodb_client_mock):
    """Create service with mocked repository."""
    with mock.patch("betor.services.bulk_update_items_service.ItemsRepository"):
        service = BulkUpdateItemsService(mongodb_client_mock)
        service.items_repository = mock.AsyncMock()  # Simple mock
        return service
```

**Key points**:
- `mongodb_client_mock` is `mock.AsyncMock(spec=...)` (type-safe)
- Patch `ItemsRepository` class
- Replace with simple `mock.AsyncMock()` (no custom classes)
- Set method return values in tests

---

### Test Implementation Pattern

```python
class TestBulkUpdateItemsServiceDispatchMaintenanceTasks:
    """Test ONLY business logic."""

    @pytest.mark.asyncio
    async def test_dispatch_one_task_per_item(
        self, bulk_update_items_service, item
    ):
        """Verify one Celery task per item."""
        items = [{"_id": f"item-{i}", **item} for i in range(3)]

        # Mock: repository returns 3 items
        bulk_update_items_service.items_repository.collection.find.return_value = items

        with mock.patch("betor.celery.app.celery_app") as celery_mock:
            sig_mock = mock.MagicMock()
            sig_mock.return_value.delay.return_value.id = "uuid"
            celery_mock.signature = sig_mock

            result = await bulk_update_items_service.dispatch_maintenance_tasks()

        # Assert: business logic
        assert sig_mock.call_count == 3
        assert len(result.task_ids) == 3
```

**Why this works**:
1. Service calls `repository.collection.find()` → we mock return value
2. Service loops over items → we count the Celery calls
3. Service returns response → we assert structure
4. **No mocking of Motor cursor**. Simple.

---

## Implementation Checklist

- [ ] Remove `MockCursor` class from test file
- [ ] Remove complex `__aiter__` and async iteration mocks
- [ ] Keep only 2 test cases:
  - [ ] `test_dispatch_one_task_per_item()`
  - [ ] `test_response_structure()`
- [ ] Use simple `mock.AsyncMock()` for repository
- [ ] Mock `collection.find.return_value = items` (list, not cursor)
- [ ] Mock `celery_app.signature()` and assert call count
- [ ] Run pytest and verify tests pass
- [ ] Delete `.md` files that were created during exploration

---

## File Structure

```
tests/betor/services/
├── test_bulk_update_items_service.py  ← THIS FILE
│   ├── Imports
│   ├── Fixtures
│   │   ├── mongodb_client_mock()
│   │   └── bulk_update_items_service()
│   └── TestBulkUpdateItemsServiceDispatchMaintenanceTasks
│       ├── test_dispatch_one_task_per_item()
│       └── test_response_structure()
```

---

## Running Tests

```bash
# Run specific test file
poetry run pytest tests/betor/services/test_bulk_update_items_service.py -v

# Run with coverage
poetry run pytest tests/betor/services/test_bulk_update_items_service.py -v --cov

# Run single test
poetry run pytest tests/betor/services/test_bulk_update_items_service.py::TestBulkUpdateItemsServiceDispatchMaintenanceTasks::test_dispatch_one_task_per_item -v
```

---

## Common Pitfalls to Avoid

| Pitfall | Example | Fix |
|---------|---------|-----|
| Custom mock class | `class MockCursor: ...` | Use `mock.AsyncMock()` |
| Mocking cursor chain | `cursor.sort.return_value = cursor` | Mock repository return value |
| Testing async iteration | `async for item in cursor` | Let Motor handle it |
| Too many test cases | 6+ cases | 2 focused cases |
| Testing library behavior | Verifying `limit()` works | Trust Motor/Celery |
| Complex return setup | `__aiter__.return_value = ...` | `return_value = items` |

---

## Reference Pattern

**Working Example**: `tests/betor/services/test_admin_download_items_service.py`

Lines to study:
- 17-18: `mongodb_client_mock` fixture
- 25-32: Service fixture with patched repository
- 50-60: Typical test structure (mock dependency, assert call)

Copy this pattern. Don't innovate.

---

## Next Steps

1. Read `TESTING_PATTERNS.md` (in same directory)
2. Implement 2 test cases per checklist
3. Run pytest
4. Verify tests pass
5. Commit changes
6. Create PR

---

## Questions?

Refer to:
- `TESTING_PATTERNS.md` - General guidelines
- `test_admin_download_items_service.py` - Working example
- `betor/services/bulk_update_items_service.py` - Service implementation
- `betor/services/admin_bulk_update_item_service.py` - Related service example
