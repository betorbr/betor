# Bulk Update Items Maintenance Endpoint — SPEC

**Objective**: Disparar tarefas de manutenção em items antigos com campos faltando ou desatualizados.

**Scope**: FastAPI endpoint + Celery service + conditional task dispatching

---

## WHAT

### Endpoint: `POST /api/v1/admin/bulk-update-items/`

**Purpose**: Recuperar items que precisam atualização (ordenados por `updated_at` DESC) e disparar tarefas Celery para cada um.

**Request Payload**:
```json
{
  "limit": 50,
  "exclude_updated_within_days": 30
}
```

**Request Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Máximo de items a processar |
| `exclude_updated_within_days` | int | 30 | Excluir items atualizados dentro de X dias |

**Response** (200 OK):
```json
{
  "task_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
  ],
  "processed_count": 3,
  "excluded_count": 47,
  "total_available": 50
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `task_ids` | List[str] | UUIDs das tasks Celery disparadas |
| `processed_count` | int | Quantidade de items para os quais tasks foram criadas |
| `excluded_count` | int | Quantidade de items excluídos pelo filtro `exclude_updated_within_days` |
| `total_available` | int | Total de items sem o filtro de data (apenas limit) |

---

## HOW

### Filter Logic (MongoDB Query)

```python
# Base query: items ordenados por updated_at DESC
query = {}

# Se exclude_updated_within_days é passado:
if exclude_updated_within_days:
    cutoff_date = datetime.now(UTC) - timedelta(days=exclude_updated_within_days)
    query["updated_at"] = {"$lt": cutoff_date}  # Mais antigos que X dias

# Fetch com limite
items = db.items.find(query).sort("updated_at", -1).limit(limit)
```

### Celery Task: `admin_bulk_update_item`

**Dispatcher** (no endpoint):
- Para cada item encontrado, dispara: `admin_bulk_update_item.delay(item_id)`
- Coleta os task IDs
- Retorna lista + counts

**Task Logic** (nova task Celery):

A task `admin_bulk_update_item` roda como wrapper que delega para `AdminBulkUpdateItemService.process()`.

Inside `AdminBulkUpdateItemService.process(item_id)`:
1. Fetch item by ID
2. Validate magnet_uri exists
3. Queue tasks **independently** (não em chain):
   - Se `download_path` é NULL → queue `update_item_torrent_info`
   - **Sempre** queue `update_item_torrent_trackers_info`
4. Ambas rodam em paralelo via `celery_app.signature(task_name).delay(args)`

**Decisão de Design:** Tasks rodam em paralelo (não sequencial via chain). Isso é seguro porque:
- `update_item_torrent_info` popula `download_path`
- `update_item_torrent_trackers_info` atualiza `torrent_num_peers`, `seeds`
- São atualizações independentes sem dependência de ordem

---

## Acceptance Criteria

- [ ] Endpoint `/api/v1/admin/bulk-update-items/` funciona com defaults (limit=50, exclude_updated_within_days=30)
- [ ] Query recupera items ordenados por `updated_at` DESC
- [ ] Query exclui items atualizados dentro de X dias
- [ ] Cada item disparado gera 1 ou 2 tasks Celery paralelos (não chain)
- [ ] Task Celery `admin_bulk_update_item` checa `download_path` e dispara `update_item_torrent_info` apenas se NULL
- [ ] Task Celery SEMPRE dispara `update_item_torrent_trackers_info`
- [ ] Tasks disparam em paralelo via `celery_app.signature().delay()` (não chain)
- [ ] Resposta retorna `task_ids`, `processed_count`, `excluded_count`
- [ ] Counts são precisos (processados + excluídos = total_available)

---

## Edge Cases

| Caso | Comportamento |
|------|---------------|
| 0 items após filtro | `processed_count=0`, `task_ids=[]`, sem erro |
| `limit` > docs na coleção | Retorna quantos existem |
| `exclude_updated_within_days=0` | Inclui items de hoje (cutoff = 00:00 hoje) |
| Item sem `magnet_uri` | Pula, log warning (nunca deve ocorrer) |
| Task falha? | Celery retry standard (já configurado globalmente) |

---

## Files to Create/Modify

**Create**:
- `betor/api/v1/admin/bulk_update_items/router.py` — Endpoint
- `betor/api/v1/admin/bulk_update_items/schema.py` — Pydantic models
- `betor/services/bulk_update_items_service.py` — Lógica de query + dispatch

**Modify**:
- `betor/celery/tasks.py` — Nova task `process_item_maintenance`
- `betor/api/v1/admin/__init__.py` — Incluir novo router

**No changes needed**:
- Existing Celery tasks (`update_item_torrent_info`, `update_item_torrent_trackers_info`) não mudam
- ItemsRepository — usar métodos existentes
