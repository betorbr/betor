# Unit Testing Patterns & Mocking Guidelines

**Status**: Established Practice | Verified: 2026-08-30

---

## Executive Summary

**Core Principle**: Trust the library. Test the business logic.

We test **what our code does**, not **how external libraries work**. Unit tests verify:
- ✅ Business logic (counts, dispatch decisions, response structure)
- ✅ Dependencies are called correctly (mocked and asserted)

We do NOT test:
- ❌ How Motor handles cursor chaining
- ❌ How Celery dispatches tasks internally
- ❌ How async iteration works in external libraries
- ❌ Data transformation by libraries (JSON, datetime, etc.)

---

## Established Fixture Pattern

**Reference Implementation**: `tests/betor/services/test_admin_download_items_service.py`

### Template

```python
from unittest import mock
import motor.motor_asyncio
import pytest

@pytest.fixture
def mongodb_client_mock():
    """Mock MongoDB AsyncIO client."""
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)

@pytest.fixture
def service_under_test(mongodb_client_mock):
    """Create service with mocked dependencies."""
    with mock.patch("betor.services.my_service.ItemsRepository"):
        service = MyService(mongodb_client_mock)
        service.items_repository = mock.AsyncMock()  # Simple mock
        return service
```

**Key Points**:
1. `mongodb_client_mock` uses `mock.AsyncMock(spec=...)` for type safety
2. Patch repository class at import time in service module
3. Replace with simple `mock.AsyncMock()` — no custom classes
4. Set return values on methods directly (`.return_value = ...`)

---

## What TO Test

### Pattern 1: Dependency Call Count

```python
@pytest.mark.asyncio
async def test_dispatches_one_task_per_item(service):
    """Verify correct number of dependency calls."""
    items = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

    # Mock repository to return items
    service.items_repository.collection.find.return_value = items

    with mock.patch("betor.celery.app.celery_app") as celery_mock:
        sig_mock = mock.MagicMock()
        celery_mock.signature = sig_mock

        await service.dispatch_tasks()

    # Assert: exactly 3 calls (business logic verification)
    assert sig_mock.call_count == 3
```

### Pattern 2: Response Structure & Counts

```python
@pytest.mark.asyncio
async def test_response_has_correct_counts(service, item_fixture):
    """Verify response structure and values."""
    items = [item_fixture] * 5
    service.items_repository.collection.find.return_value = items

    result = await service.dispatch_tasks()

    # Assert: structure and counts match business requirements
    assert isinstance(result, ResponseModel)
    assert result.total_items == 5
    assert len(result.task_ids) == 5
    assert hasattr(result, "processed_count")
```

### Pattern 3: Error Handling

```python
@pytest.mark.asyncio
async def test_raises_when_repository_fails(service):
    """Verify error propagation."""
    service.items_repository.collection.find.side_effect = RuntimeError("DB error")

    with pytest.raises(RuntimeError):
        await service.dispatch_tasks()
```

---

## What NOT to Test

### ❌ Library Implementation Details

**Example: Motor Cursor Chaining**
```python
# WRONG: Testing Motor library behavior
def test_cursor_chaining():
    cursor = create_motor_cursor()
    sorted_cursor = cursor.sort("_id", -1)
    limited = sorted_cursor.limit(10)
    # This tests Motor, not our code!
```

**Why**: Motor is maintained and tested by Mongo team. If cursor chaining breaks, it's a Motor bug or our service code usage error—both found through integration tests, not unit tests.

**Correct approach**: Mock repository to return items. Period.

---

### ❌ Async Iteration Details

```python
# WRONG: Testing Motor's async iteration
def test_async_iteration():
    cursor = motor_cursor()
    items = [item async for item in cursor]
    # This tests Motor, not our code!
```

**Why**: Motor handles async iteration. Our code just consumes it with `async for`. The iteration protocol is Motor's responsibility.

**Correct approach**: Mock repository returns list of items. Motor's async iteration is tested by Motor.

---

### ❌ Date Filtering Logic (Belongs to Repository)

```python
# WRONG: Testing repository's date filter
@pytest.mark.asyncio
async def test_date_filtering_logic():
    old_item = {**item, "updated_at": now - timedelta(days=30)}
    recent_item = {**item, "updated_at": now - timedelta(days=1)}
    # Setup complex mocks to test date logic...
    # This belongs in repository tests!
```

**Why**: Date filtering is `ItemsRepository.find_old_items()` logic. Test it in `test_items_repository.py`, not in the service that calls it.

**Correct approach**:
- In service tests: Assert repository method was called
- In repository tests: Assert date filtering works correctly

---

### ❌ Limit Parameter Behavior

```python
# WRONG: Testing Motor's limit() implementation
def test_limit_reduces_results():
    cursor = create_motor_cursor()
    limited = cursor.limit(50)
    # This tests Motor's limit(), not our code!
```

**Why**: `cursor.limit(50)` is Motor's API. It's tested by Motor. Our code just calls it. If it breaks, it's Motor's bug.

**Correct approach**: Mock repository. Assume `limit()` works. Our service doesn't re-implement `limit()`.

---

### ❌ Celery Task Registration

```python
# WRONG: Testing Celery's task dispatch mechanism
def test_celery_task_dispatch():
    # Mocking Celery internals, task registration, delay()...
    # This tests Celery, not our code!
```

**Why**: Task dispatch is Celery's responsibility. Our code just calls `celery_app.signature(...).delay()`.

**Correct approach**: Mock `celery_app.signature()` and assert it was called with correct args. Celery is tested by Celery team.

---

## Integration Tests vs Unit Tests

| Aspect | Unit Test | Integration Test |
|--------|-----------|------------------|
| **What's mocked** | Dependencies (repository, Celery) | Nothing or very minimal |
| **What works** | Our service code | Our code + real Motor/Celery |
| **How** | Fast, isolated | Slow, needs Docker/services |
| **Finds bugs** | Business logic errors | Library integration errors |
| **Example** | "For 5 items, dispatch 5 tasks" | "Cursor chaining works with real MongoDB" |

**Our focus**: Unit tests verify business logic. Integration tests (acceptance tests) verify library integration.

---

## Common Mistakes

### ❌ Mistake 1: Creating Custom Mock Classes

```python
# WRONG
class MockCursor:
    def sort(self, *args): return self
    def limit(self, *args): return self
    def __aiter__(self): ...

cursor = MockCursor(items)
service.items_repository.collection.find.return_value = cursor
```

**Why it fails**: Over-engineered. Trying to replicate Motor's behavior.

**Fix**: `service.items_repository.collection.find.return_value = items` (simple list)

---

### ❌ Mistake 2: Mocking Cursor Chain Details

```python
# WRONG
cursor.sort.return_value = cursor
cursor.limit.return_value = cursor
cursor.__aiter__.return_value = _async_iter(items)
```

**Why it fails**: `async for` doesn't work well with `__aiter__.return_value` on MagicMock.

**Fix**: Don't mock the cursor at all. Mock what the repository returns.

---

### ❌ Mistake 3: Too Many Test Cases

```python
# WRONG: 6+ test cases for one method
test_dispatch_returns_empty_when_no_items()
test_dispatch_applies_date_filter_correctly()
test_dispatch_respects_limit()
test_dispatch_excludes_recently_updated_items()
test_dispatch_returns_response_model()
# ... etc
```

**Why it fails**: Tests library behavior, not business logic. Date filtering and limit are tested elsewhere.

**Fix**: 2 focused tests:
1. Does it dispatch N tasks for N items?
2. Does the response have the right structure?

---

## Test File Template

```python
from unittest import mock
import motor.motor_asyncio
import pytest

from betor.api.v1.admin.schemas import ResponseModel
from betor.entities import Item
from betor.services.my_service import MyService

@pytest.fixture
def mongodb_client_mock():
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)

@pytest.fixture
def service(mongodb_client_mock):
    with mock.patch("betor.services.my_service.ItemsRepository"):
        svc = MyService(mongodb_client_mock)
        svc.items_repository = mock.AsyncMock()
        return svc

class TestMyServiceBusinessLogic:
    """Test ONLY business logic, not library details."""

    @pytest.mark.asyncio
    async def test_core_behavior_1(self, service, item):
        """Test: Does it do its job correctly?"""
        items = [item] * 3
        service.items_repository.some_method.return_value = items

        with mock.patch("betor.celery.app.celery_app") as celery_mock:
            sig_mock = mock.MagicMock()
            celery_mock.signature = sig_mock

            result = await service.do_something()

        assert sig_mock.call_count == 3
        assert isinstance(result, ResponseModel)

    @pytest.mark.asyncio
    async def test_core_behavior_2(self, service):
        """Test: Does response have correct structure?"""
        service.items_repository.some_method.return_value = []

        result = await service.do_something()

        assert isinstance(result, ResponseModel)
        assert hasattr(result, "field_1")
        assert hasattr(result, "field_2")
```

---

## Guidelines for New Services

When creating tests for a new service:

1. **Look at reference**: `test_admin_download_items_service.py`
2. **Copy fixture pattern**: Don't innovate
3. **Ask**: "Am I testing my code or a library?"
   - If library: Don't test it
   - If my code: Test business logic, not details
4. **Keep mocks simple**: `mock.AsyncMock()`, not custom classes
5. **Test 2-3 core scenarios**: Not every edge case (that's integration test job)
6. **Assert**: Counts, dispatch calls, response structure — NOT library mechanics

---

## Decision Tree

```
Testing a service method?
├─ Does it call a dependency (repository, Celery)?
│  └─ YES → Mock the dependency, assert it was called correctly ✅
│
├─ Does it involve a library (Motor, Celery, Redis)?
│  └─ YES → Mock it at the dependency level. Don't test library internals ✅
│
├─ Is this testing Motor cursor chaining?
│  └─ YES → DON'T. Trust Motor. Test repository instead. ❌
│
├─ Is this testing Celery task dispatch mechanics?
│  └─ YES → DON'T. Mock celery_app.signature() and assert call count. ❌
│
├─ Am I creating custom Mock classes to simulate library behavior?
│  └─ YES → STOP. Use simple mock.AsyncMock(). ❌
│
└─ Does this test my business logic (counts, decisions, structure)?
   └─ YES → Good test. Keep it. ✅
```

---

## Validation

**This pattern is proven in**:
- `tests/betor/services/test_admin_download_items_service.py` ✅
- All other existing service tests ✅

**Anti-pattern warnings** (what went wrong in `test_bulk_update_items_service.py`):
1. Created `MockCursor` class → Over-engineered ❌
2. Mocked Motor cursor chaining → Library responsibility ❌
3. Tested 6 cases → Some were library behavior ❌
4. Custom async iteration mocks → Motor handles this ❌

---

## Summary

| Do | Don't |
|----|-------|
| Mock dependencies | Mock library internals |
| Assert call counts | Test library features |
| Test business logic | Test library behavior |
| Use simple mocks | Create custom mock classes |
| 2-3 focused tests | 6+ edge case tests |
| `mock.AsyncMock()` | `__aiter__` mocking |
| Trust libraries | Replicate library features |

**Remember**: If a test requires understanding Motor internals, it's an integration test, not a unit test.

---

## Document History

- **2026-08-30**: Created after refactoring `test_bulk_update_items_service.py`
- **Reference**: Established pattern from `test_admin_download_items_service.py`
- **Lesson learned**: Focus on business logic, trust libraries
- **Status**: Authoritative guide for all new service tests in BeTor
