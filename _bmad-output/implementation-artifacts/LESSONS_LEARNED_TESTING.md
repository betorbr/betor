# Lessons Learned: Test Implementation Mistakes

**Date**: 2026-08-30
**Context**: Refactoring `test_bulk_update_items_service.py`
**Status**: Documented to prevent future iterations

---

## Timeline of Mistakes

### Iteration 1: Over-Complicated Motor Mock

**What Happened**:
- Created complex `AsyncMockCursor` class to simulate Motor cursor behavior
- Mocked `__aiter__()` and `__anext__()` methods
- Tried to replicate Motor's async iteration protocol

**Why It Failed**:
```python
# Error: TypeError: 'async_generator' object is not iterable
cursor.__aiter__.return_value = _async_iter(items)  # Motor doesn't work this way
async for item in cursor: ...  # Fails because __aiter__ returns coroutine
```

**Feedback Received**:
> "veja como subimos o fixture do mongo nos outros testes"
> (Look at how we set up MongoDB fixture in other tests)

**Lesson**: Stop innovating. Look at established patterns in `test_admin_download_items_service.py`.

---

### Iteration 2: Rigid Cursor Chaining Mock

**What Happened**:
- Mocked `find().sort().limit()` chain manually
- Set return values for each method in sequence
- Expected `async for` to work with mocked chain

**Why It Failed**:
```python
cursor.sort.return_value = cursor
cursor.limit.return_value = cursor
cursor.__aiter__.return_value = _async_iter(items)  # Still doesn't work

async for item in cursor.limit(50):  # Fails at runtime
    # TypeError: 'async_generator' object is not iterable
```

**Root Cause**: MagicMock doesn't handle async iteration properly. Trying to mock Motor's internal protocol.

**Feedback Received**:
> "opa te parei novamente, vc ta exagerando nos testes"
> (Stopped you again, you're over-testing)

> "olhe para as outras baterias não fazemos testes de retorno do banco ou algo do tipo. confiamos na biblioteca"
> (Look at other test suites—we don't test bank returns. We trust the library)

**Lesson**: Motor's async iteration is Motor's responsibility. Don't mock it.

---

### Iteration 3: Custom MockCursor Class

**What Happened**:
- Created entire class to simulate Motor cursor
- Implemented `sort()`, `limit()`, `__aiter__()`, `__anext__()`
- Tried to make it "properly" async

**Why It Failed**:
```python
class MockCursor:
    def sort(self, *args): return self
    def limit(self, *args): return self
    def __aiter__(self): return self._async_gen()
    async def _async_gen(self): ...
```

Still the same problem: mocking Motor's internals instead of testing our code.

**Feedback Received**:
> "parei mais uma vez, vc criou novamente classes para essa desgraça de mock"
> (Stopped you again, you created more custom mock classes for this mock mess)

**Lesson**: STOP creating helper classes. Use `mock.AsyncMock()`. Trust libraries.

---

## Root Cause Analysis

### Thinking Like Integration Test, Not Unit Test

**Integration Test Mindset** (WRONG):
- "How does Motor cursor actually work?"
- "I need to perfectly simulate Motor's protocol"
- "I need to make async iteration work exactly like Motor"
- Result: Over-mocked, fragile, tests library not code

**Unit Test Mindset** (CORRECT):
- "Does my service call Celery signature N times?"
- "Does my response have correct structure?"
- "Did I call repository correctly?"
- Result: Simple, focused, tests business logic

### Confused Responsibilities

**Motor's Job**: Cursor chaining, async iteration, database queries
**Celery's Job**: Task dispatch, retry logic, task registration
**Our Code's Job**: Loop through items, count them, dispatch tasks

I was testing Motor's and Celery's jobs, not ours.

---

## The Correct Pattern

### From Established Reference

**File**: `tests/betor/services/test_admin_download_items_service.py`
**Lines**: 17-32

```python
@pytest.fixture
def mongodb_client_mock():
    return mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)

@pytest.fixture
def admin_download_items_service(mongodb_client_mock, redis_client_mock):
    with mock.patch("betor.services.admin_download_items_service.ItemsRepository"):
        service = AdminDownloadItemsService(mongodb_client_mock, redis_client_mock)
        service.items_repository = mock.AsyncMock()  # That's it!
        return service
```

**In test**:
```python
service.items_repository.dump_all_items.return_value = (duration, items)
# Or:
service.items_repository.collection.find.return_value = items_list
```

**Key insight**: Simple. No custom classes. No cursor mocking. No async iteration mocking.

---

## Decision Framework

**Before implementing a test, ask**:

1. **What am I testing?**
   - If: "Does my code do X?" → Unit test ✅
   - If: "Does Motor do X?" → Don't test, trust Motor ❌

2. **Should I mock this?**
   - If: It's a dependency (repository, Celery, Redis) → Mock it ✅
   - If: It's a library (Motor cursor, Celery dispatch) → Don't mock internals ❌

3. **Can I use `mock.AsyncMock()`?**
   - If: Yes → Use it ✅
   - If: No, need custom class → Wrong approach ❌

4. **Am I testing library behavior?**
   - If: Yes (cursor chaining, async iteration, etc.) → Delete test ❌
   - If: No, testing my code → Keep test ✅

---

## Anti-Patterns to Never Repeat

| Anti-Pattern | Example | Why It's Wrong | What To Do |
|--------------|---------|-----------------|-----------|
| Custom mock class | `class MockCursor: ...` | Over-engineered, tests library | Use `mock.AsyncMock()` |
| Mock `__aiter__` | `cursor.__aiter__.return_value = ...` | Motor handles this | Let Motor work |
| Cursor chaining mock | `cursor.sort().return_value.limit()` | Motor's responsibility | Mock repository return |
| Async iteration test | `async for item in cursor` | Tests Motor, not our code | Mock repository returns list |
| 6+ test cases | Too many edge cases | Some test library behavior | 2 focused cases |
| Library internals | Testing `limit()`, `sort()`, etc. | Not our code | Trust the library |

---

## Key Takeaways

### ✅ What We Test
- Count consistency (correct number of items processed)
- Dependency call count (called Celery N times)
- Response structure (has expected fields)
- Business logic (dispatch logic, error handling)

### ❌ What We Don't Test
- Motor cursor mechanics
- Motor async iteration
- Celery task dispatch internals
- Database query behavior
- Library features (limit, sort, etc.)

### 📋 How We Test
1. Mock dependencies (repository, Celery)
2. Set mock return values
3. Call service method
4. Assert: counts, call counts, response structure
5. Done. Don't mock library internals.

### 🎯 The Principle
**Trust the library. Test the business logic.**

---

## Verification Checklist

- ✅ No custom mock classes
- ✅ No `__aiter__` mocking
- ✅ No cursor chaining setup
- ✅ No async iteration tests
- ✅ Simple `mock.AsyncMock()` for repository
- ✅ 2 focused test cases
- ✅ Test counts and structure, not library behavior
- ✅ Follows `test_admin_download_items_service.py` pattern

---

## For Future Reference

When implementing tests for ANY new service:

1. **Read**: `TESTING_PATTERNS.md`
2. **Copy**: Fixture pattern from `test_admin_download_items_service.py`
3. **Test**: Business logic only (counts, dispatch, structure)
4. **Trust**: Libraries (Motor, Celery, Redis)
5. **Avoid**: Custom mock classes, library internals, edge cases

If you find yourself creating a custom mock class or mocking `__aiter__`, **STOP**.
You're testing a library, not your code. Delete that test.

---

## Files Affected

- `tests/betor/services/test_bulk_update_items_service.py` — Needs refactoring
- Reference: `tests/betor/services/test_admin_download_items_service.py` — Pattern to follow
- Documentation: `TESTING_PATTERNS.md`, `BULK_UPDATE_ITEMS_TEST_GUIDE.md`

---

**Status**: This document should be reviewed before any further test implementation. Use as a checklist to avoid repeating mistakes.
