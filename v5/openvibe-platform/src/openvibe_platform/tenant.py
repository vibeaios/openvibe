"""Tenant management for the OpenVibe Platform."""
from __future__ import annotations

from pathlib import Path


class TenantNotFound(Exception):
    pass


class TenantStore:
    """In-memory store of tenant configurations loaded from YAML or passed directly."""

    def __init__(self, tenants: list[dict]) -> None:
        self._tenants = {t["id"]: t for t in tenants}

    def list(self) -> list[dict]:
        return list(self._tenants.values())

    def get(self, tenant_id: str) -> dict:
        if tenant_id not in self._tenants:
            raise TenantNotFound(tenant_id)
        return self._tenants[tenant_id]

    def data_dir(self, tenant_id: str) -> Path:
        return Path(self.get(tenant_id)["data_dir"])
