import pytest
from openvibe_platform.human_loop import HumanLoopService, ApprovalRequest, Deliverable


def test_create_approval_request():
    svc = HumanLoopService()
    req = svc.request_approval(
        role_id="cro", action="commit_deal",
        context={"deal_id": "d-123", "amount": 50000},
        requested_by="cro",
    )
    assert req.id is not None
    assert req.status == "pending"


def test_list_pending_approvals():
    svc = HumanLoopService()
    svc.request_approval("cro", "commit_deal", {}, "cro")
    svc.request_approval("cro", "change_pricing", {}, "cro")
    pending = svc.list_pending()
    assert len(pending) == 2


def test_approve_request():
    svc = HumanLoopService()
    req = svc.request_approval("cro", "commit_deal", {}, "cro")
    svc.approve(req.id, approved_by="charles")
    updated = svc.get(req.id)
    assert updated.status == "approved"
    assert updated.approved_by == "charles"


def test_reject_request():
    svc = HumanLoopService()
    req = svc.request_approval("cro", "commit_deal", {}, "cro")
    svc.reject(req.id, rejected_by="charles", reason="too risky")
    updated = svc.get(req.id)
    assert updated.status == "rejected"
    assert updated.rejection_reason == "too risky"


def test_stage_deliverable():
    svc = HumanLoopService()
    d = svc.stage_deliverable(
        role_id="cro", type="weekly_report",
        content="This week: 42 leads qualified.",
        metadata={"week": "2026-W08"},
    )
    assert d.id is not None
    assert d.status == "pending_review"


def test_list_deliverables():
    svc = HumanLoopService()
    svc.stage_deliverable("cro", "report", "content A", {})
    svc.stage_deliverable("cro", "report", "content B", {})
    items = svc.list_deliverables(role_id="cro")
    assert len(items) == 2


def test_acknowledge_deliverable():
    svc = HumanLoopService()
    d = svc.stage_deliverable("cro", "report", "content", {})
    svc.acknowledge_deliverable(d.id, by="charles")
    updated = svc.get_deliverable(d.id)
    assert updated.status == "acknowledged"
