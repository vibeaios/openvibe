import pytest
from openvibe_platform.workspace import WorkspaceService
from openvibe_sdk.models import WorkspaceConfig, WorkspacePolicy


def test_create_and_get_workspace():
    svc = WorkspaceService()
    ws = WorkspaceConfig(id="vibe-team", name="Vibe Team",
                         owner="charles", policy=WorkspacePolicy())
    svc.create(ws)
    found = svc.get("vibe-team")
    assert found is not None
    assert found.name == "Vibe Team"


def test_create_duplicate_raises():
    svc = WorkspaceService()
    ws = WorkspaceConfig(id="ws1", name="WS1", owner="x", policy=WorkspacePolicy())
    svc.create(ws)
    with pytest.raises(ValueError, match="already exists"):
        svc.create(ws)


def test_delete_workspace():
    svc = WorkspaceService()
    ws = WorkspaceConfig(id="ws-del", name="Del", owner="x", policy=WorkspacePolicy())
    svc.create(ws)
    svc.delete("ws-del")
    assert svc.get("ws-del") is None


def test_list_workspaces():
    svc = WorkspaceService()
    for i in range(3):
        svc.create(WorkspaceConfig(id=f"ws-{i}", name=f"WS {i}",
                                   owner="x", policy=WorkspacePolicy()))
    assert len(svc.list()) == 3


def test_get_nonexistent_returns_none():
    svc = WorkspaceService()
    assert svc.get("nobody") is None
