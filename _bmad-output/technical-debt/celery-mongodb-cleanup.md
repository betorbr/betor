# Technical Debt: Celery Task MongoDB Connection Cleanup

**Severity**: 🔴 MEDIUM (Memory leak potential)
**Category**: Resource Management
**Created**: 2026-08-30
**Related**: Code Review Finding P0.1
**Sprint**: Backlog

---

## Problem Statement

Celery task wrapper functions in `betor/celery/tasks.py` do not properly close MongoDB connections when exceptions occur during task execution.

### Current Pattern (UNSAFE)

```python
def _admin_bulk_update_item(item_id: str, **kwargs):
    mongodb_client = get_mongodb_client()
    from betor.services.admin_bulk_update_item_service import AdminBulkUpdateItemService
    service = AdminBulkUpdateItemService(mongodb_client)
    result = asyncio.run(service.process(item_id))
    mongodb_client.close()  # ← Only called on success
    return result
```

**Issue**: If `service.process()` raises an exception, `mongodb_client.close()` is never called.

### Affected Tasks

Scan identified the following affected tasks in `betor/celery/tasks.py`:

1. `_process_raw_item()` — ✅ Has try/finally (safe)
2. `_update_item_torrent_info()` — ❌ No cleanup
3. `_update_item_languages_info()` — ❌ No cleanup
4. `_update_item_episodes_info()` — ❌ No cleanup (complex, has multiple service calls)
5. `_update_item_torrent_trackers_info()` — ❌ No cleanup
6. `_admin_bulk_update_item()` — ❌ No cleanup (NEW)
7. `_tmdb_api_request()` — N/A (no MongoDB client)

---

## Impact

### Direct Impact
- **Connection Leak**: Each failed task leaves one unclosed MongoDB connection
- **Memory Leak**: Connections accumulate in async loop
- **Task Queue Degradation**: Over time, MongoDB connection pool exhausts, causing task failures
- **Cascade Failure**: System becomes increasingly unreliable as uptime increases

### Timeline
- **Immediate**: No visible impact (connection pool is large)
- **Hours to Days**: Memory usage slowly increases
- **Days to Weeks**: Pool exhausted, new tasks timeout/fail
- **Result**: Silent service degradation requiring restart

---

## Root Cause Analysis

### Why This Exists
1. Original code written without considering async exception paths
2. `_process_raw_item()` was patched (has try/finally) but others weren't
3. No linting rule or pattern enforcement for resource cleanup
4. Celery task convention in project not formalized

### Why It Wasn't Caught Earlier
- Memory leaks in production take weeks to manifest
- Most tasks succeed (low error rate), so issue is rare
- No monitoring on MongoDB connection pool usage
- No load/stress testing with failure injection

---

## Solution

### Recommended Fix (Apply to All Tasks)

```python
def _update_item_torrent_info(magnet_uri: str, **kwargs):
    mongodb_client = get_mongodb_client()
    try:
        service = UpdateItemTorrentInfoService(mongodb_client)
        result = asyncio.run(service.update(magnet_uri))
        return result
    finally:
        mongodb_client.close()
```

### Implementation Plan

**Phase 1** (Immediate - P0):
- [ ] Audit all task wrappers in `betor/celery/tasks.py`
- [ ] Apply `try/finally` pattern to tasks 2-6 above
- [ ] Write unit test validating `finally` execution

**Phase 2** (Week 1 - P1):
- [ ] Add helper function to standardize cleanup:
  ```python
  @contextlib.asynccontextmanager
  async def get_mongodb_for_task():
      client = get_mongodb_client()
      try:
          yield client
      finally:
          client.close()
  ```
- [ ] Refactor tasks to use helper (cleaner code)

**Phase 3** (Week 2 - P2):
- [ ] Add linting rule to detect missing cleanup (custom pylint rule or docstring enforcement)
- [ ] Document pattern in [AGENTS.md](../../AGENTS.md) under "Celery Task Guidelines"
- [ ] Add checklist item to new task PR template

---

## Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_celery_task_closes_mongodb_on_exception():
    """Verify MongoDB client is closed even when task raises."""
    mock_client = mock.AsyncMock()

    with mock.patch("betor.databases.mongodb.get_mongodb_client", return_value=mock_client):
        with mock.patch("betor.services.UpdateItemTorrentInfoService") as service_mock:
            service_mock.return_value.update.side_effect = RuntimeError("Task failed")

            with pytest.raises(RuntimeError):
                _update_item_torrent_info("magnet:?test")

            # Verify close was called despite exception
            mock_client.close.assert_called_once()
```

### Integration Test

Run task with simulated MongoDB failure:
```bash
# Temporarily break MongoDB connection
docker-compose stop mongodb

# Trigger task that should fail gracefully
curl -X POST http://localhost:5555/api/v1/admin/...

# Verify no connection leak (check log for proper cleanup message)
```

---

## Acceptance Criteria

- [ ] All Celery tasks in `betor/celery/tasks.py` have try/finally blocks
- [ ] Unit tests verify close() called on exception
- [ ] No new memory usage growth after 24h sustained workload with errors
- [ ] Pattern documented in code comments
- [ ] Pattern added to AGENTS.md guidelines

---

## Risk Assessment

| Aspect | Risk | Mitigation |
|--------|------|-----------|
| **Implementation Complexity** | Low | Simple try/finally pattern, no logic changes |
| **Regression Risk** | Very Low | Only adds cleanup, doesn't change success path |
| **Testing Coverage** | Medium | Needs exception-injection testing |
| **Backward Compatibility** | None | No API changes |
| **Performance Impact** | None | Cleanup is no-op for successful tasks |

---

## Effort Estimate

- **Phase 1** (Audit + fix): 2-3 hours
- **Phase 2** (Helper refactor): 1-2 hours
- **Phase 3** (Lint rule + docs): 2-3 hours
- **Total**: ~6-8 hours (can batch with other tech debt)

---

## Priority Justification

**Current**: Backlog (not urgent, but important)
**Escalate to P0 if**:
- Production incidents with connection pool exhaustion occur
- Sustained load testing reveals memory leak
- New Celery tasks added without cleanup

---

## References

- MongoDB Motor Async Cleanup: https://motor.readthedocs.io/en/stable/tutorial-tornado.html#connecting
- Python try/finally: https://docs.python.org/3/tutorial/errors.html#defining-clean-up-actions
- Project Code Review: [code-review-findings.md](../code-review-findings.md#-4-missing-resource-cleanup-on-error-in-celery-wrapper)

---

## Assigned To

- **Discovery**: Code Review (bmad-code-review) — 2026-08-30
- **Estimation**: TBD
- **Implementation**: TBD
- **Testing**: TBD
