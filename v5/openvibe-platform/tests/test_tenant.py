import pytest
from pathlib import Path
from openvibe_platform.tenant import TenantStore, TenantNotFound


def _store():
    return TenantStore(tenants=[
        {"id": "vibe-inc", "name": "Vibe Inc", "data_dir": "/tmp/vibe"},
        {"id": "astrocrest", "name": "Astrocrest", "data_dir": "/tmp/astro"},
    ])


def test_list_tenants():
    store = _store()
    tenants = store.list()
    assert len(tenants) == 2
    assert tenants[0]["id"] == "vibe-inc"


def test_get_tenant():
    store = _store()
    t = store.get("vibe-inc")
    assert t["name"] == "Vibe Inc"


def test_get_missing_raises():
    store = _store()
    with pytest.raises(TenantNotFound):
        store.get("unknown")


def test_data_dir_for_tenant():
    store = _store()
    assert store.data_dir("vibe-inc") == Path("/tmp/vibe")
