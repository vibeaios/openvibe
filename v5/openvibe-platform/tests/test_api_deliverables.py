"""Tests for deliverables endpoints (legacy /api/v1 and tenant-scoped)."""


def test_list_empty(client):
    r = client.get("/api/v1/deliverables")
    assert r.status_code == 200
    assert r.json() == []


def test_list_and_filter_by_role(client):
    svc = client.app.state.human_loop_svc
    svc.stage_deliverable("cro", "report", "Q1 Summary", {})
    svc.stage_deliverable("cmo", "brief", "Campaign Brief", {})
    r = client.get("/api/v1/deliverables?role_id=cro")
    assert len(r.json()) == 1
    assert r.json()[0]["role_id"] == "cro"


def test_view_deliverable(client):
    svc = client.app.state.human_loop_svc
    d = svc.stage_deliverable("cro", "report", "Full Report Content", {})
    r = client.get(f"/api/v1/deliverables/{d.id}")
    assert r.status_code == 200
    assert r.json()["content"] == "Full Report Content"


def test_acknowledge(client):
    svc = client.app.state.human_loop_svc
    d = svc.stage_deliverable("cro", "report", "content", {})
    r = client.post(f"/api/v1/deliverables/{d.id}/acknowledge", json={"by": "alice"})
    assert r.status_code == 200
    assert svc.get_deliverable(d.id).status == "acknowledged"


def test_tenant_deliverable_isolation(client):
    vibe_svc = client.app.state.tenant_human_loop_svcs["vibe-inc"]
    vibe_svc.stage_deliverable("cro", "report", "Q1", {})
    r = client.get("/tenants/astrocrest/deliverables")
    assert r.status_code == 200
    assert len(r.json()) == 0
