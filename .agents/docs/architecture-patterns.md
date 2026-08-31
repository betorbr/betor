# BeTor Architecture Patterns & Conventions

This document codifies patterns observed in the BeTor codebase to maintain consistency and help new features follow established conventions.

## 🏗️ Service Architecture

### Principle: Thin Wrappers, Fat Services

**Celery tasks** should be thin orchestration wrappers (5-10 lines).
**Services** should contain all business logic.

#### Wrong Pattern ❌
```python
def _process_item(item_id: str, **kwargs):
    # 60+ lines of business logic
    # - Database queries
    # - Decision logic
    # - Service calls
    # - Result aggregation
```

#### Correct Pattern ✅
```python
def _process_item(item_id: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = ProcessItemService(mongodb_client)
    result = asyncio.run(service.process(item_id))
    mongodb_client.close()
    return result
```

**Why?**
- Services are testable (mock dependencies)
- Logic is reusable (API, CLI, other tasks can call services)
- Tasks stay focused on async/retry orchestration
- Clearer separation of concerns

---

## 📛 Naming Conventions

### Service Files and Classes

#### Admin Services
Admin operations (manual, batch, or operator-triggered) use the `admin_` prefix:

**File pattern:** `admin_<action>_<entities>_service.py`
**Class pattern:** `Admin<Action><Entities>Service`

**Examples:**
| File | Class | Purpose |
|------|-------|---------|
| `admin_determines_imdb_tmdb_id_service.py` | `AdminDeterminesIMDBTMDBIdService` | Determine IDs for multiple items |
| `admin_normalize_items_tmdb_id_service.py` | `AdminNormalizeItemsTMDBIdService` | Normalize TMDB IDs |
| `admin_bulk_update_item_service.py` | `AdminBulkUpdateItemService` | Process one item in bulk update context |
| `admin_bulk_update_items_service.py` | `BulkUpdateItemsService` | Dispatch bulk update (orchestrator) |

#### Domain Services
Regular domain services (non-admin, often called by multiple code paths):

**File pattern:** `<action>_<entity>_service.py`
**Class pattern:** `<Action><Entity>Service`

**Examples:**
| File | Class | Purpose |
|------|-------|---------|
| `process_raw_item_service.py` | `ProcessRawItemService` | Process scraped raw item |
| `update_item_torrent_info_service.py` | `UpdateItemTorrentInfoService` | Fetch and store torrent metadata |
| `search_service.py` | `SearchService` | Search items |

### Celery Task Functions and Registrations

#### Admin Tasks
**Function name:** `_admin_<action>_<entity>`
**Registered as:** `admin_<action>_<entity>` (no leading underscore)

#### Domain Tasks
**Function name:** `_<action>_<entity>`
**Registered as:** `<action>_<entity>` (no leading underscore)

**Examples:**
```python
# Admin task
def _admin_bulk_update_item(item_id: str, **kwargs):
    ...

admin_bulk_update_item = celery_app.task(...)

# Domain task
def _process_raw_item(provider_slug: str, provider_url: str, **kwargs):
    ...

process_raw_item = celery_app.task(...)
```

---

## 🔄 Orchestration Pattern: Dispatcher + Worker

When an endpoint needs to process multiple items, split responsibility:

### 1. Dispatcher Service
- **What:** Queries database, applies filters, enqueues tasks
- **Where:** Called by endpoint/admin router
- **Returns:** Task IDs, counts, metadata
- **Example:** `BulkUpdateItemsService.dispatch_maintenance_tasks()`

```python
class BulkUpdateItemsService:
    async def dispatch_maintenance_tasks(self, limit: int, exclude_updated_within_days: int):
        # Query items with filters
        items = await collection.find(query).sort(...).limit(limit)

        # Enqueue task for each
        for item in items:
            admin_bulk_update_item.delay(item_id)

        # Return metadata
        return {"task_ids": [...], "processed_count": 3, "excluded_count": 47}
```

### 2. Worker Service
- **What:** Processes ONE item, decides sub-tasks, executes them
- **Where:** Called by Celery task only
- **Returns:** Detailed results per item
- **Example:** `AdminBulkUpdateItemService.process()`

```python
class AdminBulkUpdateItemService:
    async def process(self, item_id: str):
        # Fetch item
        item = await self.items_repository.get_by_id(item_id)

        # Decide which tasks to run
        tasks = []
        if item.download_path is None:
            tasks.append("update_torrent_info")
        tasks.append("update_tracker_info")

        # Execute and collect results
        results = []
        for task_name in tasks:
            result = await self._execute_task(task_name, item)
            results.append(result)

        return {"item_id": item_id, "tasks": results}
```

### 3. Glue: Celery Task
- **What:** Thin wrapper that instantiates service and calls it
- **Where:** Registered with Celery
- **Lines:** ~8-10
- **Example:** `_admin_bulk_update_item()`

```python
def _admin_bulk_update_item(item_id: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = AdminBulkUpdateItemService(mongodb_client)
    result = asyncio.run(service.process(item_id))
    mongodb_client.close()
    return result
```

### Flow Diagram
```
POST /api/v1/admin/bulk-update-items/ (Endpoint)
  ↓
BulkUpdateItemsService.dispatch_maintenance_tasks()  (Dispatcher)
  ├─ Query: find stale items
  ├─ For each item: admin_bulk_update_item.delay(item_id)
  └─ Return: {task_ids: [...], counts: {...}}

  ↓ (Async, Background)

Celery Worker: _admin_bulk_update_item(item_id)  (Glue)
  ↓
AdminBulkUpdateItemService.process(item_id)  (Worker)
  ├─ Fetch item
  ├─ Decide tasks (conditional logic)
  ├─ Execute UpdateItemTorrentInfoService
  ├─ Execute UpdateItemTorrentTrackersInfoService
  └─ Return: {item_id, tasks: [{status, result}...]}

  ↓ (Result stored via after_return hook)
```

---

## 📦 Service Structure Template

```python
from typing import Any, Dict, List

import motor.motor_asyncio

from betor.repositories.items_repository import ItemsRepository


class Admin<Action><Entities>Service:
    """
    Admin service to <verb> <entities>.

    Responsibility: <One-line description of what it does>
    """

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        """Initialize with database client."""
        self.mongodb_client = mongodb_client
        self.items_repository = ItemsRepository(mongodb_client)

    async def process(self, item_id: str) -> Dict[str, Any]:
        """
        Process a single item.

        Args:
            item_id: The item's ObjectId as string

        Returns:
            Dict with item_id and operation results
        """
        # Fetch data
        item = await self.items_repository.get_by_id(item_id)
        if not item:
            return {"error": "Item not found", "item_id": item_id}

        # Business logic here
        # ...

        return {"item_id": item_id, "result": result}
```

---

## ✅ Checklist for New Admin Features

Before creating an admin feature, verify:

- [ ] **Service naming:** `admin_<action>_<entity>_service.py` → `Admin<Action><Entity>Service`
- [ ] **Service pattern:** `__init__(mongodb_client)`, async methods
- [ ] **Service location:** `betor/services/`
- [ ] **Service exported:** Added to `betor/services/__init__.py` in both import and `__all__`
- [ ] **Task naming:** `_admin_<action>_<entity>` function → `admin_<action>_<entity>` registered task
- [ ] **Task pattern:** Thin wrapper (~8-10 lines), delegates to service
- [ ] **Task location:** In `betor/celery/tasks.py`
- [ ] **Endpoint:** In `betor/api/v1/admin/router.py` with Pydantic request/response models
- [ ] **Request schema:** Pydantic model in dedicated `*_schemas.py` file
- [ ] **No business logic in tasks:** All logic must be in Service class

---

## 🐛 Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Business logic in task function | Untestable, not reusable, hard to debug | Move to Service class |
| Naming service without `admin_` prefix | Hard to distinguish admin from domain logic | Use `admin_<action>_<entity>` |
| Service not exported in `__init__.py` | Import errors, inconsistent patterns | Add to imports and `__all__` |
| Task function too long (>15 lines) | Violates thin-wrapper principle | Extract to Service |
| Hardcoding database access in task | Tight coupling, not testable | Inject via `__init__`, use repositories |

---

## 📚 References

**Existing Admin Services:**
- `AdminDeterminesIMDBTMDBIdService` - Determine external IDs
- `AdminNormalizeItemsTMDBIdService` - Normalize stored IDs
- `AdminMapsProviderURLIMDBService` - Map provider URLs to IMDb
- `BulkUpdateItemsService` - Dispatcher for bulk maintenance

**Existing Domain Services:**
- `ProcessRawItemService` - Scrape → normalize → store
- `UpdateItemTorrentInfoService` - Fetch torrent metadata
- `UpdateItemTorrentTrackersInfoService` - Fetch peer/seed counts
- `SearchService` - Query and return items

---

**Last updated:** 2026-08-30
**Version:** 1.0
