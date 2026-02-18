"""Tests for roles endpoints (legacy /api/v1 and tenant-scoped)."""


def test_list_roles_empty(client):
    r = client.get("/api/v1/workspaces/ws1/roles")
    assert r.status_code == 200
    assert r.json() == []


def test_spawn_role(client):
    r = client.post(
        "/api/v1/workspaces/ws1/roles/spawn",
        json={"template": "cro", "params": {"region": "us"}},
    )
    assert r.status_code == 200
    assert "role_id" in r.json()


def test_spawn_then_list(client):
    client.post("/api/v1/workspaces/ws1/roles/spawn", json={"template": "cmo", "params": {}})
    roles = client.get("/api/v1/workspaces/ws1/roles").json()
    assert len(roles) == 1


def test_inspect_role(client):
    resp = client.post(
        "/api/v1/workspaces/ws1/roles/spawn",
        json={"template": "cfo", "params": {}},
    )
    role_id = resp.json()["role_id"]
    r = client.get(f"/api/v1/roles/{role_id}")
    assert r.status_code == 200
    assert r.json()["id"] == role_id


def test_tenant_role_isolation(client):
    client.post(
        "/tenants/vibe-inc/workspaces/ws1/roles/spawn",
        json={"template": "cmo", "params": {}},
    )
    roles = client.get("/tenants/astrocrest/workspaces/ws1/roles").json()
    assert len(roles) == 0
