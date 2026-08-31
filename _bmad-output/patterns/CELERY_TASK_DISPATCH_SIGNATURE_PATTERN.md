# Celery Task Dispatch via Signature Pattern

**Status:** Decision
**Date:** 2026-08-30
**Feature:** Bulk Update Items
**Applied By:** BulkUpdateItemsService

---

## Problem

When dispatching Celery tasks from a service, the natural approach is to import the task function directly:

```python
# ❌ Creates circular dependency risk
from betor.celery.tasks import admin_bulk_update_item

# Later in service method:
task = admin_bulk_update_item.delay(item_id)
```

**The Issue:** If the task module also imports from services (even inside functions), a circular import cycle can occur:
- `betor/services/bulk_update_items_service.py` imports `betor/celery/tasks.py`
- `betor/celery/tasks.py` imports `betor/services/admin_bulk_update_item_service.py` (inside function)
- At module load time, Python may fail to resolve the circular dependency

**Previous Workaround:** Lazy import inside the method:
```python
# ✅ Works but less elegant
async def dispatch_maintenance_tasks(self, ...):
    from betor.celery.tasks import admin_bulk_update_item
    task = admin_bulk_update_item.delay(item_id)
```

---

## Solution: Celery Signature Pattern

Use `celery_app.signature(task_name)` with string-based task name registration:

```python
# ✅ Recommended approach
from betor.celery.app import celery_app

async def dispatch_maintenance_tasks(self, ...):
    # No import of task module needed
    task = celery_app.signature("admin_bulk_update_item", args=(item_id,)).delay()
    task_ids.append(task.id)
```

### Why This Works

1. **celery_app (betor/celery/app.py)** has zero imports from services
   - Only imports from settings and Kombu queue framework
   - Safe to import anywhere without circular risk

2. **Task Registration** uses string names:
   ```python
   # In betor/celery/tasks.py
   admin_bulk_update_item = celery_app.task(
       _admin_bulk_update_item,
       base=BetorCeleryTask,
       name="admin_bulk_update_item",  # ← String name used by signature
       ...
   )
   ```

3. **Runtime Resolution** via Celery's registry:
   - When `.delay()` is called, Celery looks up `"admin_bulk_update_item"` in its task registry
   - Task must be registered before calling (app initialization ensures this via `include=["betor.celery.tasks"]`)

---

## Advantages

| Aspect | Direct Import | Lazy Import | Signature (Recommended) |
|--------|----------------|-------------|----------------------|
| **Circular Import Risk** | High | Medium | None |
| **Readability** | Clear reference | Needs explanation | Clear intent |
| **Code Coupling** | Tight | Medium | Loose (string-based) |
| **Test Mocking** | Direct mock | Patch module import | Mock `celery_app.signature` |
| **Maintainability** | Task rename breaks | Task rename breaks | Only registry name matters |

---

## Implementation Checklist

✅ **For Services Dispatching Tasks:**
- [ ] Import `from betor.celery.app import celery_app` (safe, no circular risk)
- [ ] Use `celery_app.signature(task_name, args=(...)).delay()`
- [ ] Pass task name as string matching registered name in `betor/celery/tasks.py`

✅ **For Celery Task Registration:**
- [ ] Register with explicit `name="snake_case_name"` parameter
- [ ] Task wrapper function can safely import services (they import celery_app, not this module)

✅ **For Unit Tests:**
- [ ] Mock `betor.celery.app.celery_app`
- [ ] Setup `signature_mock = mock.MagicMock(); celery_app_mock.signature = signature_mock`
- [ ] Verify calls via `signature_mock.return_value.delay.return_value.id`

---

## Example: BulkUpdateItemsService

**Before (Lazy Import):**
```python
async def dispatch_maintenance_tasks(self, limit=50, exclude_updated_within_days=30):
    # ... query logic ...

    from betor.celery.tasks import admin_bulk_update_item  # Lazy import

    task_ids = []
    for item in items_to_process:
        item_id = str(item["_id"])
        task = admin_bulk_update_item.delay(item_id)
        task_ids.append(task.id)
```

**After (Signature Pattern):**
```python
from betor.celery.app import celery_app  # Safe import at top

async def dispatch_maintenance_tasks(self, limit=50, exclude_updated_within_days=30):
    # ... query logic ...

    task_ids = []
    for item in items_to_process:
        item_id = str(item["_id"])
        task = celery_app.signature("admin_bulk_update_item", args=(item_id,)).delay()
        task_ids.append(task.id)
```

**Test Mocking:**
```python
with mock.patch("betor.celery.app.celery_app") as celery_app_mock:
    sig_mock = mock.MagicMock()
    sig_mock.return_value.delay.return_value.id = "task-uuid-123"
    celery_app_mock.signature = sig_mock

    result = await service.dispatch_maintenance_tasks()

    # Verify signature was called with correct task name
    sig_mock.assert_called_with("admin_bulk_update_item", args=(item_id,))
```

---

## When to Use This Pattern

✅ **Use Signature Pattern When:**
- Dispatching tasks from services (normal case)
- You want zero circular import risk
- Task names are stable (rarely renamed)
- Testing is easier with string-based mocks

❌ **Direct Import OK When:**
- Writing task registration code itself
- Inside task modules (no circular risk by definition)
- Low-level Celery infrastructure code

---

## Related Patterns

- **Lazy Import Pattern:** Use only when signature pattern is not available
- **Celery Routing:** Task routing still uses string names in `celery_app.conf.task_routes`
- **Job Monitoring:** Use `celery_app.task()` with `BetorCeleryTask` base class for lifecycle hooks

---

## Decision Rationale

Chose **Signature Pattern** over Lazy Import because:

1. **Cleaner Architecture:** celery_app has no service dependencies, making it safe to import anywhere
2. **Future-Proof:** If celery/tasks.py ever imports more service modules, no risk of breakage
3. **Test Clarity:** Mock target is obvious (`celery_app.signature`), not hidden inside functions
4. **Celery Best Practice:** String-based task names are idiomatic in Celery for exactly this reason
5. **Consistency:** Matches existing task routing in `betor/celery/app.py` which already uses string names

---

## Metrics

- **Lines of Code Changed:** 3 (1 import, 1 signature call vs 1 lazy import)
- **Circular Import Risk:** Eliminated completely
- **Test Coverage:** 6 test cases updated, all passing
- **Performance:** Identical (Celery resolves name at dispatch time either way)

---

## See Also

- [Celery Task Queuing](#celery-task-queue) in TECH_DEBT.md (connection cleanup)
- Process context: bulk-update-items-SPEC.md
- Related code: betor/services/bulk_update_items_service.py (lines 58-66)
