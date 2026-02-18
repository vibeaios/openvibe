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
