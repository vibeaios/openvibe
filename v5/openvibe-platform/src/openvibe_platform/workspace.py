"""WorkspaceService — CRUD for workspaces (in-memory store)."""

from __future__ import annotations

from openvibe_sdk.models import WorkspaceConfig


class WorkspaceService:
    def __init__(self) -> None:
        self._store: dict[str, WorkspaceConfig] = {}

    def create(self, ws: WorkspaceConfig) -> None:
        if ws.id in self._store:
            raise ValueError(f"Workspace '{ws.id}' already exists")
        self._store[ws.id] = ws

    def get(self, workspace_id: str) -> WorkspaceConfig | None:
        return self._store.get(workspace_id)

    def delete(self, workspace_id: str) -> None:
        self._store.pop(workspace_id, None)

    def list(self) -> list[WorkspaceConfig]:
        return list(self._store.values())
