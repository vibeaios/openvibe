"""Tests for /api/v1/workspaces endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/workspaces")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_list(client):
    r = client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    assert r.status_code == 200
    assert r.json()["id"] == "ws1"
    items = client.get("/api/v1/workspaces").json()
    assert any(w["id"] == "ws1" for w in items)


def test_create_duplicate_returns_409(client):
    client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    r = client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    assert r.status_code == 409


def test_delete(client):
    client.post("/api/v1/workspaces", json={"id": "ws1", "name": "WS One", "owner": "alice"})
    r = client.delete("/api/v1/workspaces/ws1")
    assert r.status_code == 204
    items = client.get("/api/v1/workspaces").json()
    assert not any(w["id"] == "ws1" for w in items)
