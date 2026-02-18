# Platform FastAPI HTTP Layer — Design

**Date:** 2026-02-18
**Status:** Approved
**Scope:** `v4/openvibe-platform/`

---

## Context

The platform layer has five pure-Python services (`WorkspaceService`, `HumanLoopService`,
`RoleGateway`, `WebhookTranslator`, `FileMemoryStore`) with no HTTP surface. The CLI
already encodes the full URL contract — this design wires the two together.

**Decisions made:**
- File-based persistence (JSON), not in-memory or database
- HTTP exposes metadata only — dispatch (`Role.handle()`) is internal, not an endpoint
- No authentication (localhost dev, dogfood phase)

---

## File Structure

```
v4/openvibe-platform/src/openvibe_platform/
  store.py              ← JSONFileStore — generic JSON persistence
  app.py                ← FastAPI instance, lifespan, create_app(data_dir)
  routers/
    __init__.py
    workspaces.py       ← /api/v1/workspaces
    roles.py            ← /api/v1/workspaces/{ws}/roles + spawn + inspect
    approvals.py        ← /api/v1/workspaces/{ws}/approvals + approve/reject
    deliverables.py     ← /api/v1/deliverables + ack
```

**Data directory layout** (default `~/.openvibe/`):
```
~/.openvibe/
  workspaces.json
  approvals.json
  deliverables.json
  roles/{workspace_id}.json
```

---

## Persistence

`JSONFileStore` is a thin wrapper: `load(path) -> dict` and `save(path, data) -> None`.
Services remain unchanged internally. The HTTP layer (routers) calls `store.save()` after
each mutation and `store.load()` on startup via `lifespan`.

`create_app(data_dir=":memory:")` skips file I/O entirely — services use their existing
in-memory dicts. Used in tests.

---

## API Contract

### Workspaces
```
GET    /api/v1/workspaces                 → list[{id, name, owner}]
POST   /api/v1/workspaces                 {id, name, owner} → {id}  (409 if duplicate)
DELETE /api/v1/workspaces/{workspace_id}  → 204
```

### Roles
```
GET  /api/v1/workspaces/{ws}/roles          → list[{id, domains}]
POST /api/v1/workspaces/{ws}/roles/spawn    {template, params} → {role_id}
GET  /api/v1/roles/{role_id}                → {id, domains, workspace, type}
```

> Roles are stored as `Participant` metadata in the registry. `spawn` creates a registry
> entry from a `RoleSpec`; it does not instantiate a live `Role` object.

### Approvals
```
GET  /api/v1/workspaces/{ws}/approvals     → list[{id, role_id, action, status}]
POST /api/v1/approvals/{id}/approve        {approved_by} → 200
POST /api/v1/approvals/{id}/reject         {reason} → 200
```

### Deliverables
```
GET  /api/v1/deliverables?workspace=&role_id=  → list[{id, role_id, type, status}]
GET  /api/v1/deliverables/{id}                 → {id, role_id, type, content, metadata}
POST /api/v1/deliverables/{id}/acknowledge     {by} → 200
```

---

## Testing

`FastAPI.TestClient` (synchronous) + `create_app(data_dir=":memory:")` — no real server,
no filesystem. One test file per router:

```
tests/
  test_api_workspaces.py    ← CRUD + 409 on duplicate
  test_api_roles.py         ← list + spawn + inspect
  test_api_approvals.py     ← list pending + approve + reject
  test_api_deliverables.py  ← list + view + ack
```

~20 tests total, all synchronous, no external dependencies.

---

## Startup

```bash
uvicorn openvibe_platform.app:app --reload
# or with custom data dir:
VIBE_DATA_DIR=/path/to/data uvicorn openvibe_platform.app:app
```
