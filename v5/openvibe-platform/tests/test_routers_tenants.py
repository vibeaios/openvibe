"""Tests for /tenants routes."""


def test_list_tenants(client):
    resp = client.get("/tenants")
    assert resp.status_code == 200
    tenants = resp.json()
    ids = [t["id"] for t in tenants]
    assert "vibe-inc" in ids
    assert "astrocrest" in ids


def test_get_tenant(client):
    resp = client.get("/tenants/vibe-inc")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Vibe Inc"


def test_get_missing_tenant(client):
    resp = client.get("/tenants/unknown")
    assert resp.status_code == 404
