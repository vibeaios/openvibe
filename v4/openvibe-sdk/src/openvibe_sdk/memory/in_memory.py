"""In-memory store -- dict-based, for dev/test."""

from __future__ import annotations

from typing import Any

from openvibe_sdk.memory import MemoryEntry


class InMemoryStore:
    """Simple in-memory MemoryProvider for development and testing."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, MemoryEntry]] = {}

    def store(self, namespace: str, key: str, value: Any) -> None:
        if namespace not in self._store:
            self._store[namespace] = {}
        self._store[namespace][key] = MemoryEntry(
            key=key, content=value, namespace=namespace
        )

    def recall(
        self, namespace: str, query: str, limit: int = 10
    ) -> list[MemoryEntry]:
        entries = list(self._store.get(namespace, {}).values())
        if query:
            entries = [
                e
                for e in entries
                if query.lower() in str(e.content).lower()
            ]
        return entries[:limit]

    def delete(self, namespace: str, key: str) -> None:
        if namespace in self._store:
            self._store[namespace].pop(key, None)
