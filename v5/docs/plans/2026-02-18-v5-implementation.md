# OpenVibe V5 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scaffold V5 with two-tenant platform (Vibe Inc + Astrocrest), Role SDK foundation with System roles and Template registry, and Astrocrest strategy docs.

**Architecture:** Multi-tenant FastAPI platform with per-tenant `JSONFileStore` isolation; SDK v1.0.0 adds `TenantContext`, `TemplateRegistry` (builds on existing `RoleTemplate`/`RoleSpec`), and three System roles; two application tenants scaffolded as role collections with YAML configs.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, pytest, typer + rich, PyYAML

**Prototype scope:** Role internals (workflows, nodes, LangGraph) are out of scope. This plan scaffolds the structure, proves tenant isolation, and writes strategy docs.

---

## Phase 0: Housekeeping

### Task 1: Rewrite root README.md

**Files:**
- Modify: `README.md`

**Step 1: Write the new README**

Replace entire content with:

```markdown
# OpenVibe

> Cognition is becoming infrastructure.

**OpenVibe** is a multi-tenant platform for human+agent collaboration. Organizations run as role collections — AI participants with identity, memory, and authority — coordinated through a shared workspace.

## Current Version: V5

**Two customers on the platform:**
- **Vibe Inc** — GTM + product development efficiency
- **Astrocrest** — AI-Berkshire OS; creates and manages professional services companies

## Quick Nav

| Path | Contents |
|------|----------|
| `v5/docs/THESIS.md` | Core thesis |
| `v5/docs/DESIGN.md` | Architecture |
| `v5/docs/ROADMAP.md` | V5 phases |
| `v5/docs/strategy/ASTROCREST.md` | Astrocrest principles |
| `v5/openvibe-sdk/` | SDK v1.0.0 |
| `v5/openvibe-platform/` | HTTP API |
| `v5/vibe-inc/` | Vibe Inc roles |
| `v5/astrocrest/` | Astrocrest roles |

## Version History

| Version | Status | Focus |
|---------|--------|-------|
| V5 | **Current** | Two-tenant platform, Role SDK, Astrocrest |
| V4 | Frozen | vibe-ai-adoption LIVE (5 operators, 470 tests) |
| V3 | Archived | Operator pattern, Temporal + LangGraph |
| V2 | Archived | SOUL, progressive disclosure, design principles |
| V1 | Archived | Nx + Supabase + Next.js prototype |
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: simplify README for V5"
```

---

### Task 2: Rewrite root CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Write the new CLAUDE.md**

```markdown
# OpenVibe

> The first workspace designed for human+agent collaboration.

## Current Focus: V5

**Read first:** `v5/docs/THESIS.md`
**Architecture:** `v5/docs/DESIGN.md`
**Current state:** `PROGRESS.md`

## Session Resume Protocol

1. Read `PROGRESS.md` — current state and phase
2. Read `v5/docs/THESIS.md` — core thesis
3. Read `v5/docs/DESIGN.md` — architecture
4. Important milestones → pause for user confirmation

## Constraints

- Only submit complete implementations (no partial work)
- Do not leave TODOs
- New features must have tests
- Two teammates should not edit the same file simultaneously

## Design Principles

1. **Agent in the conversation** — AI is a participant, not a sidebar tool
2. **Progressive Disclosure** — Headline / summary / full for all agent output
3. **Workspace gets smarter** — Context, memory, knowledge compound over time
4. **Feedback is the moat** — Agent shaped by team feedback > smarter model without context
5. **Configuration over Code** — SOUL + config-driven roles, not hardcoded behavior
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: simplify CLAUDE.md for V5"
```

---

### Task 3: Rewrite root PROGRESS.md

**Files:**
- Modify: `PROGRESS.md`

**Step 1: Write the new PROGRESS.md**

```markdown
# OpenVibe Progress

> Read this first at session start, then follow Session Resume Protocol in CLAUDE.md.

---

## Current State

**Version:** V5 — Platform Prototype
**Phase:** Layer 0 — Housekeeping complete

| Package | Path | Version | Tests |
|---------|------|---------|-------|
| openvibe-sdk | `v5/openvibe-sdk/` | v1.0.0 | — |
| openvibe-runtime | `v5/openvibe-runtime/` | v1.0.0 | — |
| openvibe-platform | `v5/openvibe-platform/` | v1.0.0 | — |
| openvibe-cli | `v5/openvibe-cli/` | v1.0.0 | — |

## Key Docs

- `v5/docs/THESIS.md` — thesis
- `v5/docs/DESIGN.md` — architecture
- `v5/docs/ROADMAP.md` — V5 plan
- `v5/docs/strategy/ASTROCREST.md` — Astrocrest principles
- `v5/docs/plans/2026-02-18-v5-design.md` — design doc
- `v5/docs/plans/2026-02-18-v5-implementation.md` — this plan

## Rules

- Important milestone complete → pause for user confirmation
- No external calls without confirmation
- UI direction unclear → pause for user sketch

---

*Update this file at each phase completion.*
```

**Step 2: Commit**

```bash
git add PROGRESS.md
git commit -m "docs: simplify PROGRESS.md for V5"
```

---

### Task 4: Scaffold V5 directory structure

**Files:**
- Create: `v5/vibe-inc/` (directory)
- Create: `v5/astrocrest/` (directory)
- Create: `v5/docs/strategy/` (directory)
- Create: `v5/docs/reference/` (directory)

**Step 1: Create directories with .gitkeep**

```bash
mkdir -p v5/vibe-inc/docs v5/vibe-inc/roles v5/vibe-inc/config
mkdir -p v5/astrocrest/docs v5/astrocrest/roles v5/astrocrest/config
mkdir -p v5/docs/strategy v5/docs/reference
touch v5/vibe-inc/.gitkeep v5/astrocrest/.gitkeep
```

**Step 2: Commit**

```bash
git add v5/
git commit -m "chore(v5): scaffold directory structure"
```

---

## Phase 1: Copy V4 Packages into V5

### Task 5: Copy openvibe-sdk

**Files:**
- Create: `v5/openvibe-sdk/` (copy of `v4/openvibe-sdk/`)

**Step 1: Copy and bump version**

```bash
cp -r v4/openvibe-sdk v5/openvibe-sdk
```

Edit `v5/openvibe-sdk/src/openvibe_sdk/__init__.py`: change `__version__ = "0.3.0"` → `__version__ = "1.0.0"`

Edit `v5/openvibe-sdk/pyproject.toml`: change `version = "0.3.0"` → `version = "1.0.0"`

**Step 2: Verify tests still pass**

```bash
cd v5/openvibe-sdk && PYTHONPATH=src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

Expected: all tests pass (same count as V4: 266)

**Step 3: Commit**

```bash
git add v5/openvibe-sdk/
git commit -m "chore(v5): copy openvibe-sdk v0.3.0 → v1.0.0 base"
```

---

### Task 6: Copy openvibe-runtime

**Step 1: Copy and bump version**

```bash
cp -r v4/openvibe-runtime v5/openvibe-runtime
```

Edit `v5/openvibe-runtime/src/openvibe_runtime/__init__.py`: bump to `1.0.0`
Edit `v5/openvibe-runtime/pyproject.toml`: bump to `1.0.0`

Also update the SDK dependency reference inside `pyproject.toml` to point to `../openvibe-sdk` (relative path).

**Step 2: Verify tests**

```bash
cd v5/openvibe-runtime && PYTHONPATH=src:../openvibe-sdk/src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

Expected: 28 tests pass

**Step 3: Commit**

```bash
git add v5/openvibe-runtime/
git commit -m "chore(v5): copy openvibe-runtime v0.1.0 → v1.0.0 base"
```

---

### Task 7: Copy openvibe-platform

**Step 1: Copy and bump version**

```bash
cp -r v4/openvibe-platform v5/openvibe-platform
```

Bump version to `1.0.0` in `__init__.py` and `pyproject.toml`.
Update SDK dependency in `pyproject.toml` to `../openvibe-sdk`.

**Step 2: Verify tests**

```bash
cd v5/openvibe-platform && PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

Expected: 47 tests pass

**Step 3: Commit**

```bash
git add v5/openvibe-platform/
git commit -m "chore(v5): copy openvibe-platform v0.1.0 → v1.0.0 base"
```

---

### Task 8: Copy openvibe-cli

**Step 1: Copy and bump version**

```bash
cp -r v4/openvibe-cli v5/openvibe-cli
```

Bump version to `1.0.0`. Update SDK dependency path.

**Step 2: Verify tests**

```bash
cd v5/openvibe-cli && PYTHONPATH=src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

Expected: 13 tests pass

**Step 3: Commit**

```bash
git add v5/openvibe-cli/
git commit -m "chore(v5): copy openvibe-cli v0.1.0 → v1.0.0 base"
```

---

## Phase 2: SDK v1.0.0 — Multi-tenant Primitives

All tests run from: `v5/openvibe-sdk/`
Command prefix: `PYTHONPATH=src /tmp/openvibe-venv/bin/python -m pytest`

---

### Task 9: Add TenantContext

**Files:**
- Modify: `v5/openvibe-sdk/src/openvibe_sdk/models.py`
- Create: `v5/openvibe-sdk/tests/test_tenant_context.py`

**Step 1: Write failing test**

```python
# tests/test_tenant_context.py
from pathlib import Path
from openvibe_sdk.models import TenantContext

def test_tenant_context_fields():
    t = TenantContext(id="vibe-inc", name="Vibe Inc", data_dir=Path("/tmp/vibe"))
    assert t.id == "vibe-inc"
    assert t.name == "Vibe Inc"
    assert t.data_dir == Path("/tmp/vibe")

def test_tenant_context_default_data_dir():
    t = TenantContext(id="astrocrest", name="Astrocrest")
    assert t.data_dir == Path.home() / ".openvibe" / "astrocrest"

def test_tenant_context_slug():
    t = TenantContext(id="vibe-inc", name="Vibe Inc")
    assert t.id == "vibe-inc"  # id is the slug
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_tenant_context.py -v
```

Expected: `ImportError` or `AttributeError` — `TenantContext` not defined

**Step 3: Add TenantContext to models.py**

Add at the end of `v5/openvibe-sdk/src/openvibe_sdk/models.py`:

```python
class TenantContext(BaseModel):
    """Identity and data isolation context for a platform tenant."""
    id: str
    name: str
    data_dir: Path = None

    def model_post_init(self, __context: Any) -> None:
        if self.data_dir is None:
            object.__setattr__(self, "data_dir", Path.home() / ".openvibe" / self.id)
```

Export from `__init__.py`:
```python
from openvibe_sdk.models import TenantContext
# add "TenantContext" to __all__
```

**Step 4: Run to verify PASS**

```bash
pytest tests/test_tenant_context.py -v
```

Expected: 3 tests pass

**Step 5: Run full suite to verify no regressions**

```bash
pytest tests/ -q
```

Expected: 266 + 3 = 269 tests pass

**Step 6: Commit**

```bash
git add v5/openvibe-sdk/
git commit -m "feat(sdk): add TenantContext model"
```

---

### Task 10: Add TemplateRegistry

The SDK already has `RoleTemplate` and `RoleSpec` models. `TemplateRegistry` manages pre-built templates that tenants instantiate and override.

**Files:**
- Create: `v5/openvibe-sdk/src/openvibe_sdk/template_registry.py`
- Create: `v5/openvibe-sdk/tests/test_template_registry.py`

**Step 1: Write failing tests**

```python
# tests/test_template_registry.py
import pytest
from openvibe_sdk.template_registry import TemplateRegistry
from openvibe_sdk.models import RoleTemplate, RoleSpec

def _make_template(name: str) -> RoleTemplate:
    return RoleTemplate(
        name=name,
        soul={"identity": {"name": name, "role": "test"}},
        capabilities=[],
    )

def test_register_and_get():
    reg = TemplateRegistry()
    tmpl = _make_template("Content")
    reg.register("gtm/content-role", tmpl)
    assert reg.get("gtm/content-role") == tmpl

def test_get_missing_raises():
    reg = TemplateRegistry()
    with pytest.raises(KeyError):
        reg.get("does/not/exist")

def test_list_templates():
    reg = TemplateRegistry()
    reg.register("gtm/content-role", _make_template("Content"))
    reg.register("gtm/revenue-role", _make_template("Revenue"))
    assert sorted(reg.list()) == ["gtm/content-role", "gtm/revenue-role"]

def test_instantiate_with_overrides():
    reg = TemplateRegistry()
    reg.register("gtm/content-role", _make_template("Content"))
    spec = reg.instantiate("gtm/content-role", name_override="Vibe Content")
    assert spec.name == "Vibe Content"

def test_instantiate_without_override_uses_template_name():
    reg = TemplateRegistry()
    reg.register("gtm/content-role", _make_template("Content"))
    spec = reg.instantiate("gtm/content-role")
    assert spec.name == "Content"
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_template_registry.py -v
```

Expected: `ModuleNotFoundError` — `template_registry` not found

**Step 3: Implement TemplateRegistry**

```python
# src/openvibe_sdk/template_registry.py
"""TemplateRegistry — manage pre-built role templates for tenant instantiation."""
from __future__ import annotations

from openvibe_sdk.models import RoleSpec, RoleTemplate


class TemplateRegistry:
    """Registry of pre-built RoleTemplates. Tenants instantiate and override."""

    def __init__(self) -> None:
        self._templates: dict[str, RoleTemplate] = {}

    def register(self, template_id: str, template: RoleTemplate) -> None:
        self._templates[template_id] = template

    def get(self, template_id: str) -> RoleTemplate:
        if template_id not in self._templates:
            raise KeyError(f"Template not found: {template_id!r}")
        return self._templates[template_id]

    def list(self) -> list[str]:
        return list(self._templates.keys())

    def instantiate(self, template_id: str, name_override: str | None = None) -> RoleSpec:
        tmpl = self.get(template_id)
        name = name_override or tmpl.name
        return RoleSpec(name=name, template=template_id, soul=tmpl.soul, capabilities=tmpl.capabilities)
```

Export from `__init__.py`:
```python
from openvibe_sdk.template_registry import TemplateRegistry
# add "TemplateRegistry" to __all__
```

**Step 4: Check what fields RoleTemplate and RoleSpec actually have** (read the models first, adjust the implementation to match — don't assume).

**Step 5: Run to verify PASS**

```bash
pytest tests/test_template_registry.py -v
```

Expected: 5 tests pass

**Step 6: Full suite**

```bash
pytest tests/ -q
```

Expected: all pass

**Step 7: Commit**

```bash
git add v5/openvibe-sdk/
git commit -m "feat(sdk): add TemplateRegistry"
```

---

### Task 11: Add System Roles

System roles (Coordinator, Archivist, Auditor) are pre-instantiated roles present in every workspace.

**Files:**
- Create: `v5/openvibe-sdk/src/openvibe_sdk/system_roles.py`
- Create: `v5/openvibe-sdk/tests/test_system_roles.py`

**Step 1: Write failing tests**

```python
# tests/test_system_roles.py
from openvibe_sdk.system_roles import SYSTEM_ROLES, Coordinator, Archivist, Auditor
from openvibe_sdk.models import RoleSpec

def test_system_roles_are_role_specs():
    for role in SYSTEM_ROLES:
        assert isinstance(role, RoleSpec)

def test_system_role_names():
    names = {r.name for r in SYSTEM_ROLES}
    assert names == {"Coordinator", "Archivist", "Auditor"}

def test_coordinator_purpose():
    assert Coordinator.name == "Coordinator"

def test_archivist_purpose():
    assert Archivist.name == "Archivist"

def test_auditor_purpose():
    assert Auditor.name == "Auditor"
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_system_roles.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Implement system_roles.py**

Read `v5/openvibe-sdk/src/openvibe_sdk/models.py` to check `RoleSpec` fields, then:

```python
# src/openvibe_sdk/system_roles.py
"""System roles — built-in roles present in every workspace."""
from __future__ import annotations

from openvibe_sdk.models import RoleSpec

Coordinator = RoleSpec(
    name="Coordinator",
    soul={"identity": {"name": "Coordinator", "role": "Routes tasks, manages approvals, handles escalation"}},
    capabilities=[],
)

Archivist = RoleSpec(
    name="Archivist",
    soul={"identity": {"name": "Archivist", "role": "Manages memory, knowledge base, episodic retention"}},
    capabilities=[],
)

Auditor = RoleSpec(
    name="Auditor",
    soul={"identity": {"name": "Auditor", "role": "Tracks deliverables, metrics, feedback loop"}},
    capabilities=[],
)

SYSTEM_ROLES: list[RoleSpec] = [Coordinator, Archivist, Auditor]
```

Export from `__init__.py`:
```python
from openvibe_sdk.system_roles import SYSTEM_ROLES, Coordinator, Archivist, Auditor
# add to __all__
```

**Step 4: Run to verify PASS**

```bash
pytest tests/test_system_roles.py -v && pytest tests/ -q
```

**Step 5: Commit**

```bash
git add v5/openvibe-sdk/
git commit -m "feat(sdk): add System roles (Coordinator, Archivist, Auditor)"
```

---

## Phase 3: Platform v1.0.0 — Tenant-scoped API

All tests run from: `v5/openvibe-platform/`
Command prefix: `PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest`

---

### Task 12: Tenant config + TenantStore

**Files:**
- Create: `v5/openvibe-platform/src/openvibe_platform/tenant.py`
- Create: `v5/openvibe-platform/tests/test_tenant.py`
- Create: `v5/openvibe-platform/config/tenants.yaml`

**Step 1: Write the tenants config**

```yaml
# v5/openvibe-platform/config/tenants.yaml
tenants:
  - id: vibe-inc
    name: Vibe Inc
    data_dir: data/vibe-inc
  - id: astrocrest
    name: Astrocrest
    data_dir: data/astrocrest
```

**Step 2: Write failing tests**

```python
# tests/test_tenant.py
import pytest
from pathlib import Path
from openvibe_platform.tenant import TenantStore, TenantNotFound

def _store():
    return TenantStore(tenants=[
        {"id": "vibe-inc", "name": "Vibe Inc", "data_dir": "/tmp/vibe"},
        {"id": "astrocrest", "name": "Astrocrest", "data_dir": "/tmp/astro"},
    ])

def test_list_tenants():
    store = _store()
    tenants = store.list()
    assert len(tenants) == 2
    assert tenants[0]["id"] == "vibe-inc"

def test_get_tenant():
    store = _store()
    t = store.get("vibe-inc")
    assert t["name"] == "Vibe Inc"

def test_get_missing_raises():
    store = _store()
    with pytest.raises(TenantNotFound):
        store.get("unknown")

def test_data_dir_for_tenant():
    store = _store()
    assert store.data_dir("vibe-inc") == Path("/tmp/vibe")
```

**Step 3: Run to verify FAIL**

```bash
pytest tests/test_tenant.py -v
```

**Step 4: Implement tenant.py**

```python
# src/openvibe_platform/tenant.py
from __future__ import annotations
from pathlib import Path


class TenantNotFound(Exception):
    pass


class TenantStore:
    def __init__(self, tenants: list[dict]) -> None:
        self._tenants = {t["id"]: t for t in tenants}

    def list(self) -> list[dict]:
        return list(self._tenants.values())

    def get(self, tenant_id: str) -> dict:
        if tenant_id not in self._tenants:
            raise TenantNotFound(tenant_id)
        return self._tenants[tenant_id]

    def data_dir(self, tenant_id: str) -> Path:
        return Path(self.get(tenant_id)["data_dir"])
```

**Step 5: Run to verify PASS**

```bash
pytest tests/test_tenant.py -v && pytest tests/ -q
```

**Step 6: Commit**

```bash
git add v5/openvibe-platform/
git commit -m "feat(platform): TenantStore + tenants.yaml config"
```

---

### Task 13: Add /tenants routes

**Files:**
- Create: `v5/openvibe-platform/src/openvibe_platform/routers/tenants.py`
- Create: `v5/openvibe-platform/tests/test_routers_tenants.py`

**Step 1: Write failing tests**

```python
# tests/test_routers_tenants.py
import pytest
from fastapi.testclient import TestClient
from openvibe_platform.app import create_app

@pytest.fixture
def client():
    app = create_app(data_dir=":memory:")
    return TestClient(app)

def test_list_tenants(client):
    resp = client.get("/tenants")
    assert resp.status_code == 200
    tenants = resp.json()
    ids = [t["id"] for t in tenants]
    assert "vibe-inc" in ids
    assert "astrocrest" in ids

def test_get_tenant(client):
    resp = client.get("/tenants/vibe-inc")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Vibe Inc"

def test_get_missing_tenant(client):
    resp = client.get("/tenants/unknown")
    assert resp.status_code == 404
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_routers_tenants.py -v
```

**Step 3: Implement routers/tenants.py**

```python
# src/openvibe_platform/routers/tenants.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("")
def list_tenants(request: Request) -> list[dict]:
    return request.app.state.tenant_store.list()


@router.get("/{tenant_id}")
def get_tenant(tenant_id: str, request: Request) -> dict:
    from openvibe_platform.tenant import TenantNotFound
    try:
        return request.app.state.tenant_store.get(tenant_id)
    except TenantNotFound:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")
```

**Step 4: Wire into app.py**

In `v5/openvibe-platform/src/openvibe_platform/app.py`:
- Import `TenantStore` from `tenant.py`
- Load `tenants.yaml` (or use hardcoded defaults for `:memory:`)
- Set `app.state.tenant_store = TenantStore(...)`
- Include `tenants.router`

**Step 5: Run to verify PASS**

```bash
pytest tests/test_routers_tenants.py -v && pytest tests/ -q
```

**Step 6: Commit**

```bash
git add v5/openvibe-platform/
git commit -m "feat(platform): /tenants routes"
```

---

### Task 14: Tenant-scoped workspaces route

Migrate `/workspaces` → `/tenants/{tenant_id}/workspaces`. The existing workspaces router provides the logic; we add a tenant-scoped wrapper.

**Files:**
- Modify: `v5/openvibe-platform/src/openvibe_platform/routers/workspaces.py`
- Modify: `v5/openvibe-platform/tests/test_routers_workspaces.py`

**Step 1: Write new failing tests** (add to existing test file)

```python
def test_tenant_workspace_isolation(client):
    # Create workspace in vibe-inc
    client.post("/tenants/vibe-inc/workspaces", json={"name": "Marketing"})

    # Should NOT appear in astrocrest
    resp = client.get("/tenants/astrocrest/workspaces")
    names = [w["name"] for w in resp.json()]
    assert "Marketing" not in names

def test_tenant_workspace_create_and_list(client):
    client.post("/tenants/vibe-inc/workspaces", json={"name": "GTM"})
    resp = client.get("/tenants/vibe-inc/workspaces")
    assert resp.status_code == 200
    names = [w["name"] for w in resp.json()]
    assert "GTM" in names
```

**Step 2: Run to verify FAIL**

```bash
pytest tests/test_routers_workspaces.py::test_tenant_workspace_isolation -v
```

**Step 3: Add tenant prefix to workspace router**

Change `router = APIRouter(prefix="/workspaces")` →
`router = APIRouter(prefix="/tenants/{tenant_id}/workspaces")`

The `tenant_id` path parameter flows through to the store lookup. Use `tenant_id` to get the correct `JSONFileStore` from the tenant-scoped store map in `app.state`.

In `app.py`, build a `dict[str, JSONFileStore]` keyed by tenant_id. Pass it to workspace router via `app.state.tenant_stores`.

**Step 4: Run to verify PASS**

```bash
pytest tests/ -q
```

**Step 5: Commit**

```bash
git add v5/openvibe-platform/
git commit -m "feat(platform): tenant-scoped workspace routes with isolation"
```

---

### Task 15: Tenant-scope remaining routes + CLI --tenant flag

**Files:**
- Modify: `v5/openvibe-platform/src/openvibe_platform/routers/roles.py`
- Modify: `v5/openvibe-platform/src/openvibe_platform/routers/approvals.py`
- Modify: `v5/openvibe-platform/src/openvibe_platform/routers/deliverables.py`
- Modify: `v5/openvibe-cli/src/openvibe_cli/main.py`

**Step 1: Mirror the pattern from Task 14 for roles, approvals, deliverables**

Each router: change prefix to `/tenants/{tenant_id}/<resource>`.
Add one isolation test per router (same pattern as Task 14).

**Step 2: Add --tenant to CLI**

In `v5/openvibe-cli/src/openvibe_cli/main.py`, add global option:

```python
@app.callback()
def main(tenant: str = typer.Option("vibe-inc", "--tenant", "-t", help="Tenant ID")):
    state["tenant"] = tenant
```

All CLI commands read `state["tenant"]` and prefix their API calls with `/tenants/{tenant}/`.

**Step 3: Add CLI test**

```python
# in existing CLI test file
def test_cli_tenant_flag():
    result = runner.invoke(app, ["--tenant", "astrocrest", "workspace", "list"])
    assert result.exit_code == 0
```

**Step 4: Run full suite**

```bash
cd v5/openvibe-platform && PYTHONPATH=src:../openvibe-sdk/src:../openvibe-runtime/src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
cd v5/openvibe-cli && PYTHONPATH=src /tmp/openvibe-venv/bin/python -m pytest tests/ -q
```

**Step 5: Commit**

```bash
git add v5/openvibe-platform/ v5/openvibe-cli/
git commit -m "feat(platform+cli): tenant-scoped routes for all resources + --tenant flag"
```

---

## Phase 4: Strategy Docs

No TDD for docs. Write → review → commit.

---

### Task 16: Write v5/docs/THESIS.md

Update the thesis for the two-customer, OS model reality. Keep it to 3-4 sections: the core insight, what changed from V4, the two-customer model, and the OS layer.

```bash
git add v5/docs/THESIS.md
git commit -m "docs(v5): THESIS.md — two-customer cognition OS"
```

---

### Task 17: Write v5/docs/DESIGN.md

Cover the Role SDK architecture (Role → System Roles → Templates → Workspace), multi-tenant platform (TenantContext, TenantStore, per-tenant JSONFileStore), and package structure. Reference the design doc at `plans/2026-02-18-v5-design.md` for context.

```bash
git add v5/docs/DESIGN.md
git commit -m "docs(v5): DESIGN.md — multi-tenant Role SDK architecture"
```

---

### Task 18: Write v5/docs/ROADMAP.md

Three phases matching the Layered Execution Plan:
- Phase 0: Housekeeping (this plan)
- Phase 1: Platform multi-tenancy (this plan)
- Phase 2: Strategy artifacts (this plan)
- Phase 3: Role implementations (future plan)
- Phase 4: Astrocrest live + Vibe Inc product dev (future plan)

Include decision gates (what must be true to move to each phase).

```bash
git add v5/docs/ROADMAP.md
git commit -m "docs(v5): ROADMAP.md — phased execution plan"
```

---

### Task 19: Write v5/docs/strategy/ASTROCREST.md

This is the most important doc in the strategy layer. Cover:

1. **What Astrocrest is** — OpenVibe's own operating intelligence, not a client
2. **Core identity** — Capital allocator, company builder, flywheel hunter
3. **Primary metric** — Flywheel density (word-of-mouth velocity) above all else
4. **Decision framework** — 5-dimension scoring model (copy from OS-MODEL, don't duplicate)
5. **Investment stance** — Self-owned (AI deliverability >70%) vs JV thresholds
6. **Kill signals** — Per lifecycle stage: M3, M6, M12 signals
7. **SOUL config sketch** — Identity, philosophy, behavior, constraints in YAML

```bash
git add v5/docs/strategy/ASTROCREST.md
git commit -m "docs(astrocrest): principles + philosophy"
```

---

### Task 20: Write v5/docs/strategy/INCUBATION-LOGIC.md

Cover the six-stage lifecycle (Scan → Score → Create → Launch → Monitor → Exit/Scale) with:
- Entry criteria per stage
- Key outputs per stage
- Decision rules (when to advance, when to abort)
- The four data models: SubSegment, Brand, Company, FlyWheelMetric

```bash
git add v5/docs/strategy/INCUBATION-LOGIC.md
git commit -m "docs(astrocrest): incubation logic + lifecycle stages"
```

---

### Task 21: Write v5/docs/strategy/OS-MODEL.md

Distill from V4's GRAND-STRATEGY and 2026-02-18-os-strategy-redesign docs. Cover:
- The three-layer architecture (Brand → Sub-segment → OS)
- Sub-segment selection framework (5D scoring)
- Self-owned vs JV rules
- Current Phase 1 candidates (Catholic K-12, Jewish day schools)

```bash
git add v5/docs/strategy/OS-MODEL.md
git commit -m "docs(strategy): OS model — sub-segment selection + company architecture"
```

---

## Phase 5: Templates + Application Scaffolding

### Task 22: Write GTM role templates (YAML)

**Files:**
- Create: `v5/openvibe-sdk/templates/gtm/content-role.yaml`
- Create: `v5/openvibe-sdk/templates/gtm/revenue-role.yaml`
- Create: `v5/openvibe-sdk/templates/gtm/customer-success-role.yaml`
- Create: `v5/openvibe-sdk/templates/gtm/market-intelligence-role.yaml`

Each YAML follows this structure (prototype — soul only, capabilities empty):

```yaml
# content-role.yaml
name: Content
soul:
  identity:
    name: Content
    role: Content strategist and producer
    description: Researches segments, generates content, manages distribution
  philosophy:
    principles:
      - Quality over quantity — every piece must be worth reading
      - Segment-first — understand the audience before writing
    values:
      - Clarity
      - Relevance
      - Consistency
  behavior:
    response_style: progressive_disclosure
    proactive: true
  constraints:
    trust_level: L2
    escalation_rules: Approve all external publishing
capabilities: []  # to be implemented in Phase 3
```

```bash
git add v5/openvibe-sdk/templates/
git commit -m "feat(sdk): GTM role templates (content, revenue, CS, market-intel)"
```

---

### Task 23: Write Product Dev role templates

**Files:**
- Create: `v5/openvibe-sdk/templates/product-dev/product-ops-role.yaml`
- Create: `v5/openvibe-sdk/templates/product-dev/engineering-ops-role.yaml`
- Create: `v5/openvibe-sdk/templates/product-dev/qa-role.yaml`

Same structure as Task 22. Focus the soul identity on each role's function:
- Product Ops: feature intake, prioritization, spec writing
- Engineering Ops: PR review, tech debt, release notes
- QA: test generation, regression planning

```bash
git add v5/openvibe-sdk/templates/
git commit -m "feat(sdk): product-dev role templates (product-ops, eng-ops, qa)"
```

---

### Task 24: Write Astrocrest role templates

**Files:**
- Create: `v5/openvibe-sdk/templates/research/market-scanner-role.yaml`
- Create: `v5/openvibe-sdk/templates/research/competitive-intel-role.yaml`
- Create: `v5/openvibe-sdk/templates/research/signal-monitor-role.yaml`
- Create: `v5/openvibe-sdk/templates/lifecycle/incubator-role.yaml`
- Create: `v5/openvibe-sdk/templates/lifecycle/health-monitor-role.yaml`
- Create: `v5/openvibe-sdk/templates/lifecycle/portfolio-manager-role.yaml`

Same structure. Key soul note for Portfolio Manager: primary metric is flywheel density, not revenue.

```bash
git add v5/openvibe-sdk/templates/
git commit -m "feat(sdk): Astrocrest role templates (research + lifecycle)"
```

---

### Task 25: Scaffold vibe-inc/ application

**Files:**
- Create: `v5/vibe-inc/config/soul.yaml`
- Create: `v5/vibe-inc/config/roles.yaml`
- Create: `v5/vibe-inc/docs/README.md`

**soul.yaml** — Vibe Inc workspace identity:
```yaml
workspace:
  tenant_id: vibe-inc
  name: Vibe Inc
  description: GTM and product development efficiency for Vibe
  system_roles: [Coordinator, Archivist, Auditor]
```

**roles.yaml** — role instantiations from templates:
```yaml
roles:
  - template: gtm/revenue-role
    name: Vibe Revenue
    overrides:
      soul.constraints.trust_level: L2
  - template: gtm/content-role
    name: Vibe Content
  - template: gtm/customer-success-role
    name: Vibe CS
  - template: gtm/market-intelligence-role
    name: Vibe Market Intel
  - template: product-dev/product-ops-role
    name: Vibe Product Ops
  - template: product-dev/engineering-ops-role
    name: Vibe Eng Ops
  - template: product-dev/qa-role
    name: Vibe QA
```

**docs/README.md** — one paragraph on what Vibe Inc is using the platform for.

```bash
git add v5/vibe-inc/
git commit -m "feat(vibe-inc): scaffold application — soul + role config"
```

---

### Task 26: Scaffold astrocrest/ application

**Files:**
- Create: `v5/astrocrest/config/soul.yaml`
- Create: `v5/astrocrest/config/roles.yaml`
- Create: `v5/astrocrest/config/scoring.yaml`
- Create: `v5/astrocrest/docs/README.md`

**soul.yaml**:
```yaml
workspace:
  tenant_id: astrocrest
  name: Astrocrest
  description: OpenVibe's operating intelligence — scans markets, creates companies, manages lifecycles
  system_roles: [Coordinator, Archivist, Auditor]
```

**roles.yaml**:
```yaml
roles:
  - template: research/market-scanner-role
    name: Market Scanner
  - template: research/competitive-intel-role
    name: Competitive Intel
  - template: research/signal-monitor-role
    name: Signal Monitor
  - template: lifecycle/incubator-role
    name: Incubator
  - template: lifecycle/health-monitor-role
    name: Health Monitor
  - template: lifecycle/portfolio-manager-role
    name: Portfolio Manager
```

**scoring.yaml** — the 5-dimension framework as config:
```yaml
dimensions:
  flywheel_density:
    weight: 0.30
    description: Community tightness, word-of-mouth velocity
  ai_deliverability:
    weight: 0.25
    description: Percentage of core work AI can complete autonomously
  pain_urgency:
    weight: 0.20
    description: Budget exists, need is acute, timeline pressure
  competitive_gap:
    weight: 0.15
    description: No AI-native competitors in this sub-segment
  reach:
    weight: 0.10
    description: Accessible via Vibe channels or direct outreach
```

```bash
git add v5/astrocrest/
git commit -m "feat(astrocrest): scaffold application — soul + roles + scoring config"
```

---

## Completion Checklist

- [ ] Root files simplified (README, CLAUDE.md, PROGRESS.md)
- [ ] V5 directory structure in place
- [ ] All 4 packages copied + tests passing
- [ ] `TenantContext` in SDK
- [ ] `TemplateRegistry` in SDK
- [ ] System roles (Coordinator, Archivist, Auditor) in SDK
- [ ] `TenantStore` + tenants.yaml in Platform
- [ ] `/tenants` routes live
- [ ] All resources tenant-scoped with isolation test
- [ ] `--tenant` flag in CLI
- [ ] Strategy docs written (THESIS, DESIGN, ROADMAP, ASTROCREST, INCUBATION-LOGIC, OS-MODEL)
- [ ] All role templates (GTM + Product Dev + Astrocrest) as YAML
- [ ] vibe-inc scaffold with soul + role config
- [ ] astrocrest scaffold with soul + roles + scoring config

---

## Update PROGRESS.md after completion

Update `PROGRESS.md` to reflect V5 Phase 0+1+2 complete, with accurate test counts.
