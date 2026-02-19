"""HTTP router for deliverables — legacy /api/v1 and tenant-scoped."""

from __future__ import annotations

import dataclasses

from fastapi import APIRouter, HTTPException, Request
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
        items = svc.list_deliverables(
            role_id=role_id or None,
            workspace_id=workspace or None,
        )
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


def make_tenant_router() -> APIRouter:
    """Tenant-scoped deliverables at /tenants/{tenant_id}/deliverables."""
    router = APIRouter(tags=["tenant-deliverables"])

    def _get_svc(request: Request, tenant_id: str) -> HumanLoopService:
        svcs: dict[str, HumanLoopService] = request.app.state.tenant_human_loop_svcs
        if tenant_id not in svcs:
            raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")
        return svcs[tenant_id]

    @router.get("/tenants/{tenant_id}/deliverables")
    def list_tenant_deliverables(
        tenant_id: str, request: Request, role_id: str = ""
    ) -> list[dict]:
        svc = _get_svc(request, tenant_id)
        items = svc.list_deliverables(role_id=role_id or None)
        return [dataclasses.asdict(d) for d in items]

    return router
