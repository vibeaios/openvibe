"""HTTP router for roles — legacy /api/v1 and tenant-scoped."""

from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from openvibe_platform.store import JSONFileStore
from openvibe_sdk.registry import InMemoryRegistry, Participant


class _RoleSpawn(BaseModel):
    template: str
    params: dict = Field(default_factory=dict)


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


def make_tenant_router() -> APIRouter:
    """Tenant-scoped roles at /tenants/{tenant_id}/workspaces/{ws}/roles."""
    router = APIRouter(tags=["tenant-roles"])

    def _get_registry(request: Request, tenant_id: str) -> InMemoryRegistry:
        registries: dict[str, InMemoryRegistry] = request.app.state.tenant_registries
        if tenant_id not in registries:
            raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")
        return registries[tenant_id]

    @router.get("/tenants/{tenant_id}/workspaces/{workspace_id}/roles")
    def list_tenant_roles(tenant_id: str, workspace_id: str, request: Request) -> list[dict]:
        registry = _get_registry(request, tenant_id)
        return [dataclasses.asdict(p) for p in registry.list_roles(workspace_id)]

    @router.post("/tenants/{tenant_id}/workspaces/{workspace_id}/roles/spawn")
    def spawn_tenant_role(
        tenant_id: str, workspace_id: str, body: _RoleSpawn, request: Request
    ) -> dict:
        registry = _get_registry(request, tenant_id)
        suffix = "-".join(str(v) for v in body.params.values()) if body.params else "default"
        role_id = f"{body.template}-{suffix}".lower().replace(" ", "-")
        registry.register_participant(
            Participant(id=role_id, type="role", domains=[]),
            workspace=workspace_id,
        )
        return {"role_id": role_id}

    return router
