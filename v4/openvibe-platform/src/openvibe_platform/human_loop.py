"""HumanLoopService — approval queue and deliverable staging."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ApprovalRequest:
    id: str
    role_id: str
    action: str
    context: dict[str, Any]
    requested_by: str
    status: str = "pending"           # "pending" | "approved" | "rejected"
    approved_by: str = ""
    rejected_by: str = ""
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Deliverable:
    id: str
    role_id: str
    type: str
    content: str
    metadata: dict[str, Any]
    status: str = "pending_review"    # "pending_review" | "acknowledged"
    acknowledged_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HumanLoopService:
    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRequest] = {}
        self._deliverables: dict[str, Deliverable] = {}

    def request_approval(self, role_id: str, action: str,
                         context: dict, requested_by: str) -> ApprovalRequest:
        req = ApprovalRequest(id=str(uuid.uuid4()), role_id=role_id,
                              action=action, context=context,
                              requested_by=requested_by)
        self._approvals[req.id] = req
        return req

    def list_pending(self) -> list[ApprovalRequest]:
        return [r for r in self._approvals.values() if r.status == "pending"]

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._approvals.get(request_id)

    def approve(self, request_id: str, approved_by: str) -> None:
        req = self._approvals[request_id]
        req.status = "approved"
        req.approved_by = approved_by

    def reject(self, request_id: str, rejected_by: str, reason: str = "") -> None:
        req = self._approvals[request_id]
        req.status = "rejected"
        req.rejected_by = rejected_by
        req.rejection_reason = reason

    def stage_deliverable(self, role_id: str, type: str,
                          content: str, metadata: dict) -> Deliverable:
        d = Deliverable(id=str(uuid.uuid4()), role_id=role_id,
                        type=type, content=content, metadata=metadata)
        self._deliverables[d.id] = d
        return d

    def list_deliverables(self, role_id: str | None = None) -> list[Deliverable]:
        items = list(self._deliverables.values())
        if role_id:
            items = [d for d in items if d.role_id == role_id]
        return items

    def get_deliverable(self, deliverable_id: str) -> Deliverable | None:
        return self._deliverables.get(deliverable_id)

    def acknowledge_deliverable(self, deliverable_id: str, by: str) -> None:
        d = self._deliverables[deliverable_id]
        d.status = "acknowledged"
        d.acknowledged_by = by
