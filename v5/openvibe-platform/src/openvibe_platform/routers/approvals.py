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
