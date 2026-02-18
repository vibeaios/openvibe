# Platform FastAPI HTTP Layer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the existing platform services into a FastAPI HTTP server so the `vibe` CLI works end-to-end.

**Architecture:** `create_app(data_dir)` factory produces a FastAPI instance with four routers (workspaces, roles, approvals, deliverables). Services are injected as closures into each router via `make_router(svc, store)`. Persistence is `JSONFileStore` — flat JSON files, `default=str` for datetime. `data_dir=":memory:"` skips I/O entirely (used in tests).

**Tech Stack:** FastAPI 0.115+, httpx (TestClient), uvicorn (runtime), Pydantic v2, Python 3.12

---

## Pre-flight: Install deps into venv

```bash
/tmp/openvibe-venv/bin/pip install fastapi httpx uvicorn
```

Expected: `Successfully installed fastapi-... httpx-... uvicorn-...`

**Test command (run from `v4/openvibe-platform/`):**
```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

---

## Task 1: Update pyproject.toml dev deps

**Files:**
- Modify: `v4/openvibe-platform/pyproject.toml`

**Step 1: Add httpx and uvicorn to dev dependencies**

Replace the `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
    "httpx>=0.27",
]
serve = [
    "uvicorn>=0.29",
]
```

**Step 2: Commit**

```bash
git add v4/openvibe-platform/pyproject.toml
git commit -m "chore(platform): add httpx + uvicorn to optional deps"
```

---

## Task 2: JSONFileStore

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/store.py`
- Create: `v4/openvibe-platform/tests/test_store.py`

**Step 1: Write the failing tests**

```python
# tests/test_store.py
"""Tests for JSONFileStore."""
import pytest
from openvibe_platform.store import JSONFileStore


def test_load_missing_file(tmp_path):
    store = JSONFileStore(tmp_path)
    assert store.load("nonexistent.json") == []


def test_save_and_load(tmp_path):
    store = JSONFileStore(tmp_path)
    store.save("items.json", [{"id": "a", "name": "Alpha"}])
    assert store.load("items.json") == [{"id": "a", "name": "Alpha"}]


def test_save_creates_parent_dirs(tmp_path):
    store = JSONFileStore(tmp_path / "nested" / "dir")
    store.save("x.json", [])
    assert (tmp_path / "nested" / "dir" / "x.json").exists()


def test_save_overwrites(tmp_path):
    store = JSONFileStore(tmp_path)
    store.save("items.json", [{"id": "a"}])
    store.save("items.json", [{"id": "b"}])
    assert store.load("items.json") == [{"id": "b"}]


def test_datetime_serialized_as_string(tmp_path):
    from datetime import datetime, timezone
    store = JSONFileStore(tmp_path)
    store.save("items.json", [{"ts": datetime.now(timezone.utc)}])
    loaded = store.load("items.json")
    assert isinstance(loaded[0]["ts"], str)
```

**Step 2: Run tests to verify they fail**

```bash
cd v4/openvibe-platform
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_store.py -v
```

Expected: `ModuleNotFoundError: No module named 'openvibe_platform.store'`

**Step 3: Implement JSONFileStore**

```python
# src/openvibe_platform/store.py
"""JSONFileStore — simple file-backed persistence for platform services."""

from __future__ import annotations

import json
from pathlib import Path


class JSONFileStore:
    """Persist lists of dicts as JSON files under a base directory."""

    def __init__(self, data_dir: Path) -> None:
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def load(self, filename: str) -> list[dict]:
        """Return parsed JSON list, or [] if file does not exist."""
        path = self._dir / filename
        if not path.exists():
            return []
        return json.loads(path.read_text())

    def save(self, filename: str, data: list[dict]) -> None:
        """Overwrite file with JSON-serialized data. Datetimes → ISO strings."""
        path = self._dir / filename
        path.write_text(json.dumps(data, default=str, indent=2))
```

**Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_store.py -v
```

Expected: `5 passed`

**Step 5: Commit**

```bash
git add v4/openvibe-platform/src/openvibe_platform/store.py v4/openvibe-platform/tests/test_store.py
git commit -m "feat(platform): JSONFileStore — JSON file persistence"
```

---

## Task 3: create_app() factory + conftest

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/routers/__init__.py`
- Create: `v4/openvibe-platform/src/openvibe_platform/app.py`
- Create: `v4/openvibe-platform/tests/conftest.py`
- Create: `v4/openvibe-platform/tests/test_app_init.py`

**Step 1: Write the failing tests**

```python
# tests/test_app_init.py
"""Smoke tests for create_app()."""


def test_create_app_returns_fastapi():
    from openvibe_platform.app import create_app
    app = create_app(data_dir=":memory:")
    assert app is not None
    assert app.title == "OpenVibe Platform"


def test_app_has_api_routes():
    from openvibe_platform.app import create_app
    app = create_app(data_dir=":memory:")
    paths = {r.path for r in app.routes}
    assert "/api/v1/workspaces" in paths
    assert "/api/v1/deliverables" in paths
```

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_app_init.py -v
```

Expected: `ModuleNotFoundError: No module named 'openvibe_platform.app'`

**Step 3: Create routers package**

```python
# src/openvibe_platform/routers/__init__.py
"""HTTP routers for the OpenVibe Platform."""
```

**Step 4: Implement create_app()**

The routers don't exist yet — import them lazily after each router task. For now, create stubs.

```python
# src/openvibe_platform/app.py
"""FastAPI application factory for the OpenVibe Platform."""

from __future__ import annotations

import dataclasses
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI

from openvibe_platform.human_loop import ApprovalRequest, Deliverable, HumanLoopService
from openvibe_platform.store import JSONFileStore
from openvibe_platform.workspace import WorkspaceService
from openvibe_sdk.models import WorkspaceConfig
from openvibe_sdk.registry import InMemoryRegistry, Participant


def create_app(data_dir: str | Path | None = None) -> FastAPI:
    """Create and return a configured FastAPI application.

    Args:
        data_dir: Path to store JSON files. Use ":memory:" to skip all I/O (tests).
                  Defaults to VIBE_DATA_DIR env var, or ~/.openvibe.
    """
    if data_dir is None:
        data_dir = os.environ.get("VIBE_DATA_DIR", str(Path.home() / ".openvibe"))

    workspace_svc = WorkspaceService()
    human_loop_svc = HumanLoopService()
    registry = InMemoryRegistry()

    store: JSONFileStore | None = None
    if str(data_dir) != ":memory:":
        store = JSONFileStore(Path(str(data_dir)))
        _restore(workspace_svc, human_loop_svc, registry, store)

    app = FastAPI(title="OpenVibe Platform", version="0.1.0")

    # Store services in app.state so tests can seed data directly
    app.state.workspace_svc = workspace_svc
    app.state.human_loop_svc = human_loop_svc
    app.state.registry = registry

    # Import routers here to avoid circular imports
    from openvibe_platform.routers import approvals as approvals_router
    from openvibe_platform.routers import deliverables as deliverables_router
    from openvibe_platform.routers import roles as roles_router
    from openvibe_platform.routers import workspaces as ws_router

    app.include_router(ws_router.make_router(workspace_svc, store), prefix="/api/v1")
    app.include_router(roles_router.make_router(registry, store), prefix="/api/v1")
    app.include_router(approvals_router.make_router(human_loop_svc, store), prefix="/api/v1")
    app.include_router(deliverables_router.make_router(human_loop_svc, store), prefix="/api/v1")

    return app


def _restore(
    workspace_svc: WorkspaceService,
    human_loop_svc: HumanLoopService,
    registry: InMemoryRegistry,
    store: JSONFileStore,
) -> None:
    """Reload persisted state into in-memory services on startup."""
    for item in store.load("workspaces.json"):
        try:
            workspace_svc.create(WorkspaceConfig(**item))
        except (ValueError, Exception):
            pass

    for item in store.load("approvals.json"):
        req = ApprovalRequest(
            id=item["id"],
            role_id=item["role_id"],
            action=item["action"],
            context=item.get("context", {}),
            requested_by=item.get("requested_by", ""),
            status=item.get("status", "pending"),
            approved_by=item.get("approved_by", ""),
            rejected_by=item.get("rejected_by", ""),
            rejection_reason=item.get("rejection_reason", ""),
            created_at=(
                datetime.fromisoformat(item["created_at"])
                if isinstance(item.get("created_at"), str)
                else datetime.now(timezone.utc)
            ),
        )
        human_loop_svc._approvals[req.id] = req

    for item in store.load("deliverables.json"):
        d = Deliverable(
            id=item["id"],
            role_id=item["role_id"],
            type=item["type"],
            content=item.get("content", ""),
            metadata=item.get("metadata", {}),
            status=item.get("status", "pending_review"),
            acknowledged_by=item.get("acknowledged_by", ""),
            created_at=(
                datetime.fromisoformat(item["created_at"])
                if isinstance(item.get("created_at"), str)
                else datetime.now(timezone.utc)
            ),
        )
        human_loop_svc._deliverables[d.id] = d

    for item in store.load("roles.json"):
        registry.register_participant(
            Participant(
                id=item["id"],
                type=item.get("type", "role"),
                name=item.get("name", ""),
                domains=item.get("domains", []),
            ),
            workspace=item.get("workspace", ""),
        )


# Module-level app for uvicorn: `uvicorn openvibe_platform.app:app`
app = create_app()
```

**Step 5: Create four empty router stubs** (so `create_app` can import them)

```python
# src/openvibe_platform/routers/workspaces.py
from fastapi import APIRouter
from openvibe_platform.store import JSONFileStore
from openvibe_platform.workspace import WorkspaceService

def make_router(svc: WorkspaceService, store: JSONFileStore | None = None) -> APIRouter:
    return APIRouter()
```

```python
# src/openvibe_platform/routers/roles.py
from fastapi import APIRouter
from openvibe_platform.store import JSONFileStore
from openvibe_sdk.registry import InMemoryRegistry

def make_router(registry: InMemoryRegistry, store: JSONFileStore | None = None) -> APIRouter:
    return APIRouter()
```

```python
# src/openvibe_platform/routers/approvals.py
from fastapi import APIRouter
from openvibe_platform.human_loop import HumanLoopService
from openvibe_platform.store import JSONFileStore

def make_router(svc: HumanLoopService, store: JSONFileStore | None = None) -> APIRouter:
    return APIRouter()
```

```python
# src/openvibe_platform/routers/deliverables.py
from fastapi import APIRouter
from openvibe_platform.human_loop import HumanLoopService
from openvibe_platform.store import JSONFileStore

def make_router(svc: HumanLoopService, store: JSONFileStore | None = None) -> APIRouter:
    return APIRouter()
```

**Step 6: Create conftest.py**

```python
# tests/conftest.py
"""Shared test fixtures for platform HTTP tests."""

import pytest
from fastapi.testclient import TestClient

from openvibe_platform.app import create_app


@pytest.fixture
def client():
    """TestClient with all services in-memory (no file I/O)."""
    return TestClient(create_app(data_dir=":memory:"))
```

**Step 7: Run tests**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_app_init.py -v
```

Expected: `2 passed`

**Step 8: Commit**

```bash
git add \
  v4/openvibe-platform/src/openvibe_platform/app.py \
  v4/openvibe-platform/src/openvibe_platform/routers/__init__.py \
  v4/openvibe-platform/src/openvibe_platform/routers/workspaces.py \
  v4/openvibe-platform/src/openvibe_platform/routers/roles.py \
  v4/openvibe-platform/src/openvibe_platform/routers/approvals.py \
  v4/openvibe-platform/src/openvibe_platform/routers/deliverables.py \
  v4/openvibe-platform/tests/conftest.py \
  v4/openvibe-platform/tests/test_app_init.py
git commit -m "feat(platform): create_app() factory + router stubs + conftest"
```

---

## Task 4: Workspaces router

**Files:**
- Modify: `v4/openvibe-platform/src/openvibe_platform/routers/workspaces.py`
- Create: `v4/openvibe-platform/tests/test_api_workspaces.py`

**Step 1: Write the failing tests**

```python
# tests/test_api_workspaces.py
"""Tests for /api/v1/workspaces endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/workspaces")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_list(client):
    r = client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    assert r.status_code == 200
    assert r.json()["id"] == "ws1"
    items = client.get("/api/v1/workspaces").json()
    assert any(w["id"] == "ws1" for w in items)


def test_create_duplicate_returns_409(client):
    client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    r = client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    assert r.status_code == 409


def test_delete(client):
    client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    r = client.delete("/api/v1/workspaces/ws1")
    assert r.status_code == 204
    items = client.get("/api/v1/workspaces").json()
    assert not any(w["id"] == "ws1" for w in items)
```

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_workspaces.py -v
```

Expected: `404 Not Found` on all routes (stubs return empty router)

**Step 3: Implement workspaces router**

```python
# src/openvibe_platform/routers/workspaces.py
"""HTTP router for /api/v1/workspaces."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openvibe_platform.store import JSONFileStore
from openvibe_platform.workspace import WorkspaceService
from openvibe_sdk.models import WorkspaceConfig


class _WorkspaceCreate(BaseModel):
    id: str
    name: str
    owner: str = ""


def make_router(svc: WorkspaceService, store: JSONFileStore | None = None) -> APIRouter:
    router = APIRouter(tags=["workspaces"])

    def _save() -> None:
        if store:
            store.save("workspaces.json", [ws.model_dump() for ws in svc.list()])

    @router.get("/workspaces")
    def list_workspaces() -> list[dict]:
        return [ws.model_dump() for ws in svc.list()]

    @router.post("/workspaces", status_code=200)
    def create_workspace(body: _WorkspaceCreate) -> dict:
        try:
            svc.create(WorkspaceConfig(id=body.id, name=body.name, owner=body.owner))
        except ValueError:
            raise HTTPException(status_code=409, detail=f"Workspace '{body.id}' already exists")
        _save()
        return {"id": body.id}

    @router.delete("/workspaces/{workspace_id}", status_code=204)
    def delete_workspace(workspace_id: str) -> None:
        svc.delete(workspace_id)
        _save()

    return router
```

**Step 4: Run tests**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_workspaces.py -v
```

Expected: `4 passed`

**Step 5: Commit**

```bash
git add v4/openvibe-platform/src/openvibe_platform/routers/workspaces.py v4/openvibe-platform/tests/test_api_workspaces.py
git commit -m "feat(platform): workspaces router — list, create, delete"
```

---

## Task 5: Roles router

**Files:**
- Modify: `v4/openvibe-platform/src/openvibe_platform/routers/roles.py`
- Create: `v4/openvibe-platform/tests/test_api_roles.py`

**Step 1: Write the failing tests**

```python
# tests/test_api_roles.py
"""Tests for /api/v1/workspaces/{ws}/roles endpoints."""


def test_list_roles_empty(client):
    r = client.get("/api/v1/workspaces/ws1/roles")
    assert r.status_code == 200
    assert r.json() == []


def test_spawn_role(client):
    r = client.post(
        "/api/v1/workspaces/ws1/roles/spawn",
        json={"template": "cro", "params": {"region": "us"}},
    )
    assert r.status_code == 200
    assert "role_id" in r.json()


def test_spawn_then_list(client):
    client.post("/api/v1/workspaces/ws1/roles/spawn", json={"template": "cmo", "params": {}})
    roles = client.get("/api/v1/workspaces/ws1/roles").json()
    assert len(roles) == 1


def test_inspect_role(client):
    resp = client.post(
        "/api/v1/workspaces/ws1/roles/spawn",
        json={"template": "cfo", "params": {}},
    )
    role_id = resp.json()["role_id"]
    r = client.get(f"/api/v1/roles/{role_id}")
    assert r.status_code == 200
    assert r.json()["id"] == role_id
```

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_roles.py -v
```

Expected: `404 Not Found` on all routes

**Step 3: Implement roles router**

```python
# src/openvibe_platform/routers/roles.py
"""HTTP router for /api/v1/workspaces/{ws}/roles."""

from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openvibe_platform.store import JSONFileStore
from openvibe_sdk.registry import InMemoryRegistry, Participant


class _RoleSpawn(BaseModel):
    template: str
    params: dict = {}


def make_router(registry: InMemoryRegistry, store: JSONFileStore | None = None) -> APIRouter:
    router = APIRouter(tags=["roles"])

    def _save() -> None:
        if store:
            all_roles = []
            for ws_id, role_map in registry._store.items():
                for p in role_map.values():
                    all_roles.append({"workspace": ws_id, **dataclasses.asdict(p)})
            store.save("roles.json", all_roles)

    @router.get("/workspaces/{workspace_id}/roles")
    def list_roles(workspace_id: str) -> list[dict]:
        return [dataclasses.asdict(p) for p in registry.list_roles(workspace_id)]

    @router.post("/workspaces/{workspace_id}/roles/spawn")
    def spawn_role(workspace_id: str, body: _RoleSpawn) -> dict:
        suffix = "-".join(str(v) for v in body.params.values()) if body.params else "default"
        role_id = f"{body.template}-{suffix}".lower().replace(" ", "-")
        registry.register_participant(
            Participant(id=role_id, type="role", domains=[]),
            workspace=workspace_id,
        )
        _save()
        return {"role_id": role_id}

    @router.get("/roles/{role_id}")
    def inspect_role(role_id: str) -> dict:
        for ws_id, role_map in registry._store.items():
            if role_id in role_map:
                p = role_map[role_id]
                return {"workspace": ws_id, **dataclasses.asdict(p)}
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")

    return router
```

**Step 4: Run tests**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_roles.py -v
```

Expected: `4 passed`

**Step 5: Commit**

```bash
git add v4/openvibe-platform/src/openvibe_platform/routers/roles.py v4/openvibe-platform/tests/test_api_roles.py
git commit -m "feat(platform): roles router — list, spawn, inspect"
```

---

## Task 6: Approvals router

**Files:**
- Modify: `v4/openvibe-platform/src/openvibe_platform/routers/approvals.py`
- Create: `v4/openvibe-platform/tests/test_api_approvals.py`

**Step 1: Write the failing tests**

> Tests seed approval data directly via `client.app.state.human_loop_svc` — no need for a create endpoint.

```python
# tests/test_api_approvals.py
"""Tests for /api/v1/approvals endpoints."""


def test_list_pending_empty(client):
    r = client.get("/api/v1/workspaces/ws1/approvals")
    assert r.status_code == 200
    assert r.json() == []


def test_list_pending_shows_only_pending(client):
    svc = client.app.state.human_loop_svc
    req = svc.request_approval("cro", "send_email", {}, "cro-agent")
    svc.request_approval("cmo", "post_tweet", {}, "cmo-agent")
    svc.approve(req.id, "alice")  # one already approved
    r = client.get("/api/v1/workspaces/ws1/approvals")
    assert len(r.json()) == 1  # only the pending one


def test_approve(client):
    svc = client.app.state.human_loop_svc
    req = svc.request_approval("cro", "send_email", {}, "cro-agent")
    r = client.post(f"/api/v1/approvals/{req.id}/approve", json={"approved_by": "alice"})
    assert r.status_code == 200
    assert svc.get(req.id).status == "approved"


def test_reject(client):
    svc = client.app.state.human_loop_svc
    req = svc.request_approval("cro", "send_email", {}, "cro-agent")
    r = client.post(f"/api/v1/approvals/{req.id}/reject", json={"reason": "too risky"})
    assert r.status_code == 200
    assert svc.get(req.id).status == "rejected"
    assert svc.get(req.id).rejection_reason == "too risky"
```

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_approvals.py -v
```

Expected: `404 Not Found` on all routes

**Step 3: Implement approvals router**

```python
# src/openvibe_platform/routers/approvals.py
"""HTTP router for /api/v1/approvals."""

from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openvibe_platform.human_loop import HumanLoopService
from openvibe_platform.store import JSONFileStore


class _ApproveBody(BaseModel):
    approved_by: str = "human"


class _RejectBody(BaseModel):
    reason: str = ""


def make_router(svc: HumanLoopService, store: JSONFileStore | None = None) -> APIRouter:
    router = APIRouter(tags=["approvals"])

    def _save() -> None:
        if store:
            store.save(
                "approvals.json",
                [dataclasses.asdict(r) for r in svc._approvals.values()],
            )

    @router.get("/workspaces/{workspace_id}/approvals")
    def list_approvals(workspace_id: str) -> list[dict]:
        return [dataclasses.asdict(r) for r in svc.list_pending()]

    @router.post("/approvals/{request_id}/approve")
    def approve(request_id: str, body: _ApproveBody) -> dict:
        if not svc.get(request_id):
            raise HTTPException(status_code=404, detail=f"Approval '{request_id}' not found")
        svc.approve(request_id, body.approved_by)
        _save()
        return {}

    @router.post("/approvals/{request_id}/reject")
    def reject(request_id: str, body: _RejectBody) -> dict:
        if not svc.get(request_id):
            raise HTTPException(status_code=404, detail=f"Approval '{request_id}' not found")
        svc.reject(request_id, "human", body.reason)
        _save()
        return {}

    return router
```

**Step 4: Run tests**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_approvals.py -v
```

Expected: `4 passed`

**Step 5: Commit**

```bash
git add v4/openvibe-platform/src/openvibe_platform/routers/approvals.py v4/openvibe-platform/tests/test_api_approvals.py
git commit -m "feat(platform): approvals router — list pending, approve, reject"
```

---

## Task 7: Deliverables router

**Files:**
- Modify: `v4/openvibe-platform/src/openvibe_platform/routers/deliverables.py`
- Create: `v4/openvibe-platform/tests/test_api_deliverables.py`

**Step 1: Write the failing tests**

```python
# tests/test_api_deliverables.py
"""Tests for /api/v1/deliverables endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/deliverables")
    assert r.status_code == 200
    assert r.json() == []


def test_list_and_filter_by_role(client):
    svc = client.app.state.human_loop_svc
    svc.stage_deliverable("cro", "report", "Q1 Summary", {})
    svc.stage_deliverable("cmo", "brief", "Campaign Brief", {})
    r = client.get("/api/v1/deliverables?role_id=cro")
    assert len(r.json()) == 1
    assert r.json()[0]["role_id"] == "cro"


def test_view_deliverable(client):
    svc = client.app.state.human_loop_svc
    d = svc.stage_deliverable("cro", "report", "Full Report Content", {})
    r = client.get(f"/api/v1/deliverables/{d.id}")
    assert r.status_code == 200
    assert r.json()["content"] == "Full Report Content"


def test_acknowledge(client):
    svc = client.app.state.human_loop_svc
    d = svc.stage_deliverable("cro", "report", "content", {})
    r = client.post(f"/api/v1/deliverables/{d.id}/acknowledge", json={"by": "alice"})
    assert r.status_code == 200
    assert svc.get_deliverable(d.id).status == "acknowledged"
```

**Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/test_api_deliverables.py -v
```

Expected: `404 Not Found` on all routes

**Step 3: Implement deliverables router**

```python
# src/openvibe_platform/routers/deliverables.py
"""HTTP router for /api/v1/deliverables."""

from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openvibe_platform.human_loop import HumanLoopService
from openvibe_platform.store import JSONFileStore


class _AckBody(BaseModel):
    by: str = "human"


def make_router(svc: HumanLoopService, store: JSONFileStore | None = None) -> APIRouter:
    router = APIRouter(tags=["deliverables"])

    def _save() -> None:
        if store:
            store.save(
                "deliverables.json",
                [dataclasses.asdict(d) for d in svc._deliverables.values()],
            )

    @router.get("/deliverables")
    def list_deliverables(workspace: str = "", role_id: str = "") -> list[dict]:
        items = svc.list_deliverables(role_id=role_id or None)
        return [dataclasses.asdict(d) for d in items]

    @router.get("/deliverables/{deliverable_id}")
    def get_deliverable(deliverable_id: str) -> dict:
        d = svc.get_deliverable(deliverable_id)
        if not d:
            raise HTTPException(status_code=404, detail=f"Deliverable '{deliverable_id}' not found")
        return dataclasses.asdict(d)

    @router.post("/deliverables/{deliverable_id}/acknowledge")
    def acknowledge(deliverable_id: str, body: _AckBody) -> dict:
        d = svc.get_deliverable(deliverable_id)
        if not d:
            raise HTTPException(status_code=404, detail=f"Deliverable '{deliverable_id}' not found")
        svc.acknowledge_deliverable(deliverable_id, body.by)
        _save()
        return {}

    return router
```

**Step 4: Run full test suite**

```bash
PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

Expected: `~44 passed` (24 existing + 5 store + 2 init + 4 workspaces + 4 roles + 4 approvals + 4 deliverables)

**Step 5: Commit**

```bash
git add v4/openvibe-platform/src/openvibe_platform/routers/deliverables.py v4/openvibe-platform/tests/test_api_deliverables.py
git commit -m "feat(platform): deliverables router — list, view, acknowledge"
```

---

## Task 8: Update PROGRESS.md

**Files:**
- Modify: `PROGRESS.md` (root)

**Step 1: Update current state**

In the Current State table, update platform row:

```markdown
| `openvibe-platform` | `v4/openvibe-platform/` | v0.1.0 | ~44 passed |
```

Add to Version History under V4:
```markdown
- **Platform HTTP complete** (2026-02-18): FastAPI layer, JSON persistence, ~44 tests
```

Update timestamp to current.

**Step 2: Commit**

```bash
git add PROGRESS.md
git commit -m "docs(progress): Platform HTTP layer complete"
```
