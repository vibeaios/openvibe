"""FastAPI application factory for the OpenVibe Platform."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fastapi import FastAPI

from openvibe_platform.human_loop import ApprovalRequest, Deliverable, HumanLoopService
from openvibe_platform.store import JSONFileStore
from openvibe_platform.tenant import TenantStore
from openvibe_platform.workspace import WorkspaceService
from openvibe_sdk.models import WorkspaceConfig, WorkspacePolicy
from openvibe_sdk.registry import InMemoryRegistry, Participant

# Default tenants for :memory: mode (tests / local dev)
_DEFAULT_TENANTS = [
    {"id": "vibe-inc", "name": "Vibe Inc", "data_dir": ":memory:"},
    {"id": "astrocrest", "name": "Astrocrest", "data_dir": ":memory:"},
]

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _load_tenants(data_dir: str | Path) -> list[dict]:
    """Load tenants from config/tenants.yaml, or fall back to defaults for :memory: mode."""
    if str(data_dir) == ":memory:":
        return _DEFAULT_TENANTS

    yaml_path = _CONFIG_DIR / "tenants.yaml"
    if yaml_path.exists():
        with open(yaml_path) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("tenants", _DEFAULT_TENANTS)

    return _DEFAULT_TENANTS


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

    app = FastAPI(title="OpenVibe Platform", version="1.0.0")

    # Store services in app.state so tests can seed data directly
    app.state.workspace_svc = workspace_svc
    app.state.human_loop_svc = human_loop_svc
    app.state.registry = registry

    # Load tenants from YAML (production) or defaults (:memory: / tests)
    tenants = _load_tenants(data_dir)
    tenant_store = TenantStore(tenants)
    app.state.tenant_store = tenant_store

    # Per-tenant services (for isolated tenant-scoped routes)
    tenant_ids = [t["id"] for t in tenants]
    tenant_workspace_svcs: dict[str, WorkspaceService] = {
        tid: WorkspaceService() for tid in tenant_ids
    }
    tenant_human_loop_svcs: dict[str, HumanLoopService] = {
        tid: HumanLoopService() for tid in tenant_ids
    }
    tenant_registries: dict[str, InMemoryRegistry] = {
        tid: InMemoryRegistry() for tid in tenant_ids
    }
    app.state.tenant_workspace_svcs = tenant_workspace_svcs
    app.state.tenant_human_loop_svcs = tenant_human_loop_svcs
    app.state.tenant_registries = tenant_registries

    from openvibe_platform.routers import approvals as approvals_router
    from openvibe_platform.routers import deliverables as deliverables_router
    from openvibe_platform.routers import roles as roles_router
    from openvibe_platform.routers import tenants as tenants_router
    from openvibe_platform.routers import workspaces as ws_router

    app.include_router(ws_router.make_router(workspace_svc, store), prefix="/api/v1")
    app.include_router(roles_router.make_router(registry, store), prefix="/api/v1")
    app.include_router(approvals_router.make_router(human_loop_svc, store), prefix="/api/v1")
    app.include_router(deliverables_router.make_router(human_loop_svc, store), prefix="/api/v1")
    app.include_router(tenants_router.router)
    app.include_router(ws_router.make_tenant_router())
    app.include_router(roles_router.make_tenant_router())
    app.include_router(approvals_router.make_tenant_router())
    app.include_router(deliverables_router.make_tenant_router())

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
            workspace_id=item.get("workspace_id", ""),
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
            workspace_id=item.get("workspace_id", ""),
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
