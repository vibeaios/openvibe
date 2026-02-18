"""HTTP router for /api/v1/workspaces."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openvibe_platform.store import JSONFileStore
from openvibe_platform.workspace import WorkspaceService
from openvibe_sdk.models import WorkspaceConfig, WorkspacePolicy


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
            svc.create(WorkspaceConfig(id=body.id, name=body.name, owner=body.owner, policy=WorkspacePolicy()))
        except ValueError:
            raise HTTPException(status_code=409, detail=f"Workspace '{body.id}' already exists")
        _save()
        return {"id": body.id}

    @router.delete("/workspaces/{workspace_id}", status_code=204)
    def delete_workspace(workspace_id: str) -> None:
        svc.delete(workspace_id)
        _save()

    return router
