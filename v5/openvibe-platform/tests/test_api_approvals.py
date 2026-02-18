"""Tests for approvals endpoints (legacy /api/v1 and tenant-scoped)."""


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


def test_tenant_approval_isolation(client):
    vibe_svc = client.app.state.tenant_human_loop_svcs["vibe-inc"]
    vibe_svc.request_approval("cro", "send_email", {}, "cro-agent")
    r = client.get("/tenants/astrocrest/workspaces/ws1/approvals")
    assert r.status_code == 200
    assert len(r.json()) == 0
